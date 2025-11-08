#!/usr/bin/env python3
"""
Flask API Server for Teltonika Telemetry Data
Connects to DynamoDB and provides REST endpoints
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal
import json
from datetime import datetime, timedelta
import os

app = Flask(__name__)

# Enable CORS for GitHub Pages
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://tylerporras.github.io",
            "http://localhost:*",
            "http://127.0.0.1:*"
        ]
    }
})

# AWS Configuration
AWS_REGION = os.environ.get('AWS_DEFAULT_REGION', 'us-west-1')
TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'teltonika-events')

# Initialize DynamoDB
try:
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    table = dynamodb.Table(TABLE_NAME)
    print(f"✅ Connected to DynamoDB table: {TABLE_NAME} in region: {AWS_REGION}")
except Exception as e:
    print(f"❌ Error connecting to DynamoDB: {str(e)}")
    print("Make sure AWS credentials are set in environment variables:")
    print("  - AWS_ACCESS_KEY_ID")
    print("  - AWS_SECRET_ACCESS_KEY")
    print("  - AWS_DEFAULT_REGION")

# Helper function to convert Decimal to float for JSON serialization
def decimal_to_float(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

# Custom JSON encoder
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

app.json_encoder = DecimalEncoder

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.utcnow().isoformat(),
        'table': TABLE_NAME,
        'region': AWS_REGION
    })

@app.route('/api/latest/<imei>', methods=['GET'])
def get_latest(imei):
    """Get the latest telemetry data for a device"""
    try:
        # Query DynamoDB for latest record
        response = table.query(
            KeyConditionExpression=Key('imei').eq(imei),
            ScanIndexForward=False,  # Sort descending (newest first)
            Limit=1
        )
        
        if not response.get('Items'):
            return jsonify({'error': 'No data found for device'}), 404
        
        item = response['Items'][0]
        
        # Parse records JSON if exists
        records = []
        if 'records' in item and item['records']:
            try:
                records = json.loads(item['records'])
            except:
                records = []
        
        # Get the first record's data
        data = {}
        if records:
            data = records[0]
        
        result = {
            'imei': item.get('imei'),
            'timestamp': int(item.get('timestamp', 0)),
            'received_at': int(item.get('received_at', 0)),
            'vin': item.get('vin', 'UNKNOWN'),
            'imsi': item.get('imsi'),
            'operatorId': item.get('operatorId'),
            'codec_id': int(item.get('codec_id', 0)),
            'num_records': int(item.get('num_records', 0)),
            'data': data
        }
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error fetching latest data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/history/<imei>', methods=['GET'])
def get_history(imei):
    """Get historical data for a device"""
    try:
        # Get query parameters
        limit = int(request.args.get('limit', 100))
        hours = int(request.args.get('hours', 24))
        
        # Calculate timestamp cutoff
        cutoff = int((datetime.utcnow() - timedelta(hours=hours)).timestamp() * 1000)
        
        # Query DynamoDB
        response = table.query(
            KeyConditionExpression=Key('imei').eq(imei) & Key('timestamp').gte(cutoff),
            ScanIndexForward=False,  # Newest first
            Limit=limit
        )
        
        items = response.get('Items', [])
        
        # Parse records for each item
        for item in items:
            if 'records' in item and item['records']:
                try:
                    item['records_parsed'] = json.loads(item['records'])
                except:
                    item['records_parsed'] = []
        
        result = {
            'imei': imei,
            'count': len(items),
            'hours': hours,
            'records': items
        }
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error fetching history: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/trips/<imei>', methods=['GET'])
def get_trips(imei):
    """Get trip data grouped by ignition cycles"""
    try:
        # Get last 7 days of data
        hours = int(request.args.get('hours', 168))  # 7 days default
        cutoff = int((datetime.utcnow() - timedelta(hours=hours)).timestamp() * 1000)
        
        response = table.query(
            KeyConditionExpression=Key('imei').eq(imei) & Key('timestamp').gte(cutoff),
            ScanIndexForward=True  # Oldest first for trip analysis
        )
        
        items = response.get('Items', [])
        
        # Group into trips based on ignition
        trips = []
        current_trip = None
        
        for item in items:
            if 'records' in item and item['records']:
                try:
                    records = json.loads(item['records'])
                    if records:
                        record = records[0]
                        ignition = record.get('io', {}).get('ignition', {}).get('value', 0)
                        io = record.get('io', {})
                        trip_odo = io.get('trip_odometer', {}).get('value', 0)
                        
                        if ignition == 1:  # Ignition ON
                            if current_trip is None:
                                # Start new trip
                                current_trip = {
                                    'start_time': item['timestamp'],
                                    'start_odometer': trip_odo,
                                    'points': [],
                                    'max_speed': 0,
                                    'total_distance': 0
                                }
                            
                            # Add point to current trip
                            gps = record.get('gps', {})
                            speed = gps.get('speed_kmh', 0)
                            
                            current_trip['points'].append({
                                'timestamp': item['timestamp'],
                                'gps': gps,
                                'speed': speed,
                                'odometer': trip_odo
                            })
                            
                            current_trip['max_speed'] = max(current_trip['max_speed'], speed)
                            current_trip['end_time'] = item['timestamp']
                            current_trip['end_odometer'] = trip_odo
                            
                        elif current_trip is not None:  # Ignition OFF
                            # End current trip
                            duration_ms = current_trip['end_time'] - current_trip['start_time']
                            
                            # Calculate distance from odometer (more accurate than GPS)
                            distance_meters = current_trip['end_odometer'] - current_trip['start_odometer']
                            
                            # Calculate average speed
                            speeds = [p['speed'] for p in current_trip['points']]
                            avg_speed = sum(speeds) / len(speeds) if speeds else 0
                            
                            current_trip['duration_ms'] = duration_ms
                            current_trip['avg_speed'] = round(avg_speed, 1)
                            current_trip['num_points'] = len(current_trip['points'])
                            current_trip['total_distance'] = distance_meters
                            
                            # Remove points to reduce response size (keep first and last)
                            if len(current_trip['points']) > 2:
                                current_trip['points'] = [
                                    current_trip['points'][0],
                                    current_trip['points'][-1]
                                ]
                            
                            trips.append(current_trip)
                            current_trip = None
                            
                except Exception as e:
                    print(f"Error parsing record: {str(e)}")
                    continue
        
        # Add current trip if still ongoing
        if current_trip is not None:
            duration_ms = current_trip['end_time'] - current_trip['start_time']
            
            # Calculate distance from odometer
            distance_meters = current_trip.get('end_odometer', 0) - current_trip.get('start_odometer', 0)
            
            speeds = [p['speed'] for p in current_trip['points']]
            avg_speed = sum(speeds) / len(speeds) if speeds else 0
            
            current_trip['duration_ms'] = duration_ms
            current_trip['avg_speed'] = round(avg_speed, 1)
            current_trip['num_points'] = len(current_trip['points'])
            current_trip['total_distance'] = distance_meters
            current_trip['ongoing'] = True
            
            # Keep only first and last points to reduce size
            if len(current_trip['points']) > 2:
                current_trip['points'] = [
                    current_trip['points'][0],
                    current_trip['points'][-1]
                ]
            
            trips.append(current_trip)
        
        result = {
            'imei': imei,
            'count': len(trips),
            'trips': trips
        }
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error fetching trips: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats/<imei>', methods=['GET'])
def get_stats(imei):
    """Get statistics for a time period"""
    try:
        hours = int(request.args.get('hours', 24))
        cutoff = int((datetime.utcnow() - timedelta(hours=hours)).timestamp() * 1000)
        
        response = table.query(
            KeyConditionExpression=Key('imei').eq(imei) & Key('timestamp').gte(cutoff),
            ScanIndexForward=False
        )
        
        items = response.get('Items', [])
        
        # Calculate stats
        total_records = len(items)
        max_speed = 0
        total_distance = 0
        
        for item in items:
            if 'records' in item and item['records']:
                try:
                    records = json.loads(item['records'])
                    if records:
                        record = records[0]
                        gps = record.get('gps', {})
                        speed = gps.get('speed_kmh', 0)
                        max_speed = max(max_speed, speed)
                        
                        # Get odometer if available
                        io = record.get('io', {})
                        trip_odo = io.get('trip_odometer', {}).get('value', 0)
                        total_distance = max(total_distance, trip_odo / 1000)  # Convert to km
                        
                except:
                    continue
        
        result = {
            'imei': imei,
            'period_hours': hours,
            'total_records': total_records,
            'total_distance_km': round(total_distance, 1),
            'max_speed_kmh': round(max_speed, 1)
        }
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error calculating stats: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Starting API server on port {port}")
    print(f"📊 DynamoDB Table: {TABLE_NAME}")
    print(f"🌍 AWS Region: {AWS_REGION}")
    print(f"🔗 Endpoints:")
    print(f"   GET /api/health")
    print(f"   GET /api/latest/<imei>")
    print(f"   GET /api/history/<imei>?limit=100&hours=24")
    print(f"   GET /api/trips/<imei>?hours=168")
    print(f"   GET /api/stats/<imei>?hours=24")
    
    app.run(host='0.0.0.0', port=port, debug=False)