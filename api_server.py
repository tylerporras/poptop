"""
Flask API to serve Teltonika tracking data from DynamoDB
This provides REST endpoints for the dashboard
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import boto3
from boto3.dynamodb.conditions import Key, Attr
from decimal import Decimal
import json
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)  # Enable CORS for dashboard access

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-west-1')
table = dynamodb.Table('teltonika-events')

class DecimalEncoder(json.JSONEncoder):
    """Helper to convert DynamoDB Decimal types to JSON"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()})

@app.route('/api/latest', methods=['GET'])
def get_latest():
    """Get the latest data point for a device"""
    imei = request.args.get('imei', '862464068525406')
    
    try:
        # Query the latest record for this IMEI
        response = table.query(
            KeyConditionExpression=Key('imei').eq(imei),
            ScanIndexFilter=Attr('num_records').gt(0),
            Limit=1,
            ScanIndexForward=False  # Sort descending by timestamp
        )
        
        if response['Items']:
            item = response['Items'][0]
            
            # Parse the parsed_data JSON string
            if 'parsed_data' in item:
                parsed = json.loads(item['parsed_data'])
                
                # Get the latest record from the parsed data
                if parsed.get('records'):
                    latest_record = parsed['records'][-1]
                    
                    return jsonify({
                        'imei': item['imei'],
                        'timestamp': item['timestamp'],
                        'received_at': item.get('received_at'),
                        'data': latest_record
                    })
        
        return jsonify({'error': 'No data found'}), 404
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    """Get historical data for a device"""
    imei = request.args.get('imei', '862464068525406')
    hours = int(request.args.get('hours', 24))
    
    try:
        # Calculate timestamp for N hours ago
        cutoff_time = int((datetime.now() - timedelta(hours=hours)).timestamp() * 1000)
        
        # Query data
        response = table.query(
            KeyConditionExpression=Key('imei').eq(imei) & Key('timestamp').gt(cutoff_time),
            ScanIndexForward=True  # Sort ascending by timestamp
        )
        
        records = []
        for item in response['Items']:
            if 'parsed_data' in item:
                parsed = json.loads(item['parsed_data'])
                
                # Extract all records from this item
                if parsed.get('records'):
                    for record in parsed['records']:
                        records.append({
                            'imei': item['imei'],
                            'timestamp': record['timestamp'],
                            'datetime': record['datetime'],
                            'gps': record.get('gps', {}),
                            'io': record.get('io', {}),
                            'priority': record.get('priority', 0),
                            'event_io_id': record.get('event_io_id', 0)
                        })
        
        return jsonify({
            'imei': imei,
            'count': len(records),
            'records': records
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/trips', methods=['GET'])
def get_trips():
    """Get trip information (grouped by ignition cycles)"""
    imei = request.args.get('imei', '862464068525406')
    hours = int(request.args.get('hours', 168))  # Default 7 days
    
    try:
        # Get historical data
        cutoff_time = int((datetime.now() - timedelta(hours=hours)).timestamp() * 1000)
        
        response = table.query(
            KeyConditionExpression=Key('imei').eq(imei) & Key('timestamp').gt(cutoff_time),
            ScanIndexForward=True
        )
        
        # Collect all records
        all_records = []
        for item in response['Items']:
            if 'parsed_data' in item:
                parsed = json.loads(item['parsed_data'])
                if parsed.get('records'):
                    for record in parsed['records']:
                        all_records.append({
                            'timestamp': record['timestamp'],
                            'datetime': record['datetime'],
                            'gps': record.get('gps', {}),
                            'io': record.get('io', {}),
                            'ignition': record.get('io', {}).get('ignition', {}).get('value', 0)
                        })
        
        # Sort by timestamp
        all_records.sort(key=lambda x: x['timestamp'])
        
        # Process trips based on ignition cycles
        trips = []
        current_trip = None
        
        for record in all_records:
            ignition = record['ignition']
            
            if ignition == 1 and current_trip is None:
                # Start new trip
                current_trip = {
                    'id': len(trips) + 1,
                    'start_time': record['timestamp'],
                    'start_datetime': record['datetime'],
                    'end_time': None,
                    'end_datetime': None,
                    'start_location': record['gps'],
                    'end_location': None,
                    'points': [record],
                    'max_speed': record['gps'].get('speed_kmh', 0),
                    'distance': 0,
                    'ongoing': True
                }
            elif ignition == 1 and current_trip is not None:
                # Continue trip
                current_trip['points'].append(record)
                current_trip['end_time'] = record['timestamp']
                current_trip['end_datetime'] = record['datetime']
                current_trip['end_location'] = record['gps']
                current_trip['max_speed'] = max(
                    current_trip['max_speed'],
                    record['gps'].get('speed_kmh', 0)
                )
                
                # Calculate distance
                if len(current_trip['points']) > 1:
                    prev = current_trip['points'][-2]
                    dist = calculate_distance(
                        prev['gps'].get('latitude', 0),
                        prev['gps'].get('longitude', 0),
                        record['gps'].get('latitude', 0),
                        record['gps'].get('longitude', 0)
                    )
                    current_trip['distance'] += dist
                    
            elif ignition == 0 and current_trip is not None:
                # End trip
                current_trip['ongoing'] = False
                if not current_trip['end_time']:
                    current_trip['end_time'] = current_trip['points'][-1]['timestamp']
                    current_trip['end_datetime'] = current_trip['points'][-1]['datetime']
                    current_trip['end_location'] = current_trip['points'][-1]['gps']
                
                # Calculate duration
                current_trip['duration_ms'] = current_trip['end_time'] - current_trip['start_time']
                
                # Calculate average speed
                if current_trip['duration_ms'] > 0:
                    current_trip['avg_speed'] = (current_trip['distance'] / (current_trip['duration_ms'] / 1000)) * 3600
                else:
                    current_trip['avg_speed'] = 0
                
                trips.append(current_trip)
                current_trip = None
        
        # If there's an ongoing trip, add it
        if current_trip is not None:
            current_trip['end_time'] = current_trip['points'][-1]['timestamp']
            current_trip['end_datetime'] = current_trip['points'][-1]['datetime']
            current_trip['end_location'] = current_trip['points'][-1]['gps']
            current_trip['duration_ms'] = current_trip['end_time'] - current_trip['start_time']
            
            if current_trip['duration_ms'] > 0:
                current_trip['avg_speed'] = (current_trip['distance'] / (current_trip['duration_ms'] / 1000)) * 3600
            else:
                current_trip['avg_speed'] = 0
            
            trips.append(current_trip)
        
        # Return trips (most recent first)
        trips.reverse()
        
        return jsonify({
            'imei': imei,
            'count': len(trips),
            'trips': trips
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get overall statistics"""
    imei = request.args.get('imei', '862464068525406')
    hours = int(request.args.get('hours', 168))
    
    try:
        # Get trip data
        cutoff_time = int((datetime.now() - timedelta(hours=hours)).timestamp() * 1000)
        
        response = table.query(
            KeyConditionExpression=Key('imei').eq(imei) & Key('timestamp').gt(cutoff_time),
            ScanIndexForward=True
        )
        
        total_records = 0
        total_distance = 0
        max_speed = 0
        
        for item in response['Items']:
            if 'parsed_data' in item:
                parsed = json.loads(item['parsed_data'])
                if parsed.get('records'):
                    total_records += len(parsed['records'])
                    
                    for record in parsed['records']:
                        speed = record.get('gps', {}).get('speed_kmh', 0)
                        max_speed = max(max_speed, speed)
                        
                        trip_odo = record.get('io', {}).get('trip_odometer', {}).get('value', 0)
                        if trip_odo > total_distance:
                            total_distance = trip_odo
        
        return jsonify({
            'imei': imei,
            'period_hours': hours,
            'total_records': total_records,
            'total_distance_km': total_distance / 1000,
            'max_speed_kmh': max_speed
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two GPS coordinates in km"""
    from math import radians, sin, cos, sqrt, atan2
    
    R = 6371  # Earth's radius in km
    
    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    delta_lat = radians(lat2 - lat1)
    delta_lon = radians(lon2 - lon1)
    
    a = sin(delta_lat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    return R * c

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
