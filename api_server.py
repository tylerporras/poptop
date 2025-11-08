import json
import boto3
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta
from decimal import Decimal
import math

app = Flask(__name__)
CORS(app, origins=['https://tylerporras.github.io'])

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-west-1')
table = dynamodb.Table('teltonika-events')
vehicle_mapping_table = dynamodb.Table('vehicle-mapping')

# Convert Decimal to int/float for JSON serialization
def decimal_to_number(obj):
    """Convert Decimal objects to int or float"""
    if isinstance(obj, Decimal):
        if obj % 1 == 0:
            return int(obj)
        else:
            return float(obj)
    elif isinstance(obj, dict):
        return {k: decimal_to_number(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [decimal_to_number(item) for item in obj]
    return obj

# VIN decoder
def decode_vin(vin):
    """Decode VIN to extract basic vehicle information"""
    if not vin or len(vin) != 17:
        return {
            'make': 'Unknown',
            'model': 'Unknown',
            'year': 'Unknown',
            'country': 'Unknown'
        }
    
    # World Manufacturer Identifier (first 3 characters)
    wmi = vin[:3]
    
    # Common WMI codes
    wmi_map = {
        'WBA': {'make': 'BMW', 'country': 'Germany'},
        'WBS': {'make': 'BMW M', 'country': 'Germany'},
        '1FA': {'make': 'Ford', 'country': 'USA'},
        '1G1': {'make': 'Chevrolet', 'country': 'USA'},
        '5YJ': {'make': 'Tesla', 'country': 'USA'},
        'JTD': {'make': 'Toyota', 'country': 'Japan'},
    }
    
    vehicle_info = wmi_map.get(wmi, {'make': 'Unknown', 'country': 'Unknown'})
    
    # Try to decode BMW model from VIN position 4
    if wmi.startswith('WB'):  # BMW
        model_code = vin[3] if len(vin) > 3 else 'X'
        bmw_models = {
            'A': '3 Series',
            'B': '5 Series',
            'C': '7 Series',
            'E': '3 Series',
            'F': 'M Series',
            'G': 'X Series',
            'K': '6 Series',
        }
        vehicle_info['model'] = bmw_models.get(model_code, 'BMW Series')
    else:
        vehicle_info['model'] = 'Unknown'
    
    # Decode year (position 10)
    year_code = vin[9] if len(vin) > 9 else None
    year_map = {
        'A': 2010, 'B': 2011, 'C': 2012, 'D': 2013, 'E': 2014,
        'F': 2015, 'G': 2016, 'H': 2017, 'J': 2018, 'K': 2019,
        'L': 2020, 'M': 2021, 'N': 2022, 'P': 2023, 'R': 2024,
        'S': 2025, '5': 2005, '6': 2006, '7': 2007, '8': 2008, '9': 2009
    }
    vehicle_info['year'] = year_map.get(year_code, 'Unknown')
    
    return vehicle_info

# Calculate distance between two GPS points using Haversine formula
def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    Returns distance in meters
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of earth in meters
    r = 6371000
    
    return c * r

# Calculate trip distance from GPS points
def calculate_gps_distance(records):
    """Calculate total distance from GPS coordinates"""
    total_distance = 0
    
    for i in range(1, len(records)):
        prev = records[i-1]
        curr = records[i]
        
        # Get GPS data
        prev_gps = prev.get('gps', {})
        curr_gps = curr.get('gps', {})
        
        if prev_gps.get('valid') and curr_gps.get('valid'):
            prev_lat = prev_gps.get('latitude')
            prev_lon = prev_gps.get('longitude')
            curr_lat = curr_gps.get('latitude')
            curr_lon = curr_gps.get('longitude')
            
            if all([prev_lat, prev_lon, curr_lat, curr_lon]):
                distance = haversine_distance(prev_lat, prev_lon, curr_lat, curr_lon)
                # Only add if reasonable (less than 500m between points, accounting for 30s intervals)
                if distance < 500:
                    total_distance += distance
    
    return total_distance

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.utcnow().isoformat(),
        'table': table.table_name,
        'region': 'us-west-1'
    })

@app.route('/api/latest/<imei>', methods=['GET'])
def get_latest_data(imei):
    """Get the most recent telemetry data for a device"""
    try:
        # Query the latest record
        response = table.query(
            KeyConditionExpression='imei = :imei',
            ExpressionAttributeValues={
                ':imei': imei
            },
            ScanIndexForward=False,
            Limit=1
        )
        
        if not response['Items']:
            return jsonify({'error': 'No data found'}), 404
        
        item = response['Items'][0]
        
        # Parse the records JSON string
        records = json.loads(item.get('records', '[]'))
        latest_record = records[0] if records else {}
        
        # Convert Decimal to int/float
        result = {
            'imei': item.get('imei'),
            'timestamp': int(item.get('timestamp', 0)),
            'vin': item.get('vin'),
            'data': decimal_to_number(latest_record)
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/trips/<imei>', methods=['GET'])
def get_trips(imei):
    """Get trip history for a device"""
    try:
        # Get hours parameter (default 168 = 7 days)
        hours = int(request.args.get('hours', 168))
        
        # Calculate start time
        start_time = int((datetime.utcnow() - timedelta(hours=hours)).timestamp() * 1000)
        
        # Query DynamoDB
        response = table.query(
            KeyConditionExpression='imei = :imei AND #ts >= :start_time',
            ExpressionAttributeNames={
                '#ts': 'timestamp'
            },
            ExpressionAttributeValues={
                ':imei': imei,
                ':start_time': start_time
            },
            ScanIndexForward=True
        )
        
        items = response['Items']
        
        if not items:
            return jsonify({'count': 0, 'trips': [], 'imei': imei})
        
        # Get VIN from first record (should be same for all)
        vin = items[0].get('vin', 'Unknown')
        vehicle_info = decode_vin(str(vin)) if vin and vin != 'Unknown' else {}
        
        # Process records and group into trips
        trips = []
        current_trip = None
        
        for item in items:
            # Parse records
            records = json.loads(item.get('records', '[]'))
            
            for record in records:
                timestamp = record.get('timestamp', 0)
                io_data = record.get('io', {})
                gps_data = record.get('gps', {})
                
                # Get ignition status
                ignition = io_data.get('ignition', {}).get('value', 0)
                speed = gps_data.get('speed_kmh', 0)
                
                # Get odometer values
                trip_odometer = io_data.get('trip_odometer', {}).get('value', 0)
                total_odometer = io_data.get('total_odometer', {}).get('value', 0)
                
                # Trip start: ignition on
                if ignition == 1 and current_trip is None:
                    current_trip = {
                        'start_time': int(timestamp),
                        'start_odometer': int(trip_odometer) if trip_odometer else 0,
                        'start_total_odometer': int(total_odometer) if total_odometer else 0,
                        'max_speed': float(speed) if speed else 0,
                        'speed_sum': 0,
                        'speed_count': 0,
                        'records': [],
                        'vin': str(vin) if vin else 'Unknown',
                        'vehicle_make': vehicle_info.get('make', 'Unknown'),
                        'vehicle_model': vehicle_info.get('model', 'Unknown'),
                        'vehicle_year': vehicle_info.get('year', 'Unknown')
                    }
                
                # Trip ongoing: collect data
                if current_trip is not None:
                    current_trip['records'].append(record)
                    current_trip['end_time'] = int(timestamp)
                    current_trip['end_odometer'] = int(trip_odometer) if trip_odometer else 0
                    current_trip['end_total_odometer'] = int(total_odometer) if total_odometer else 0
                    
                    # Update max speed
                    if speed and speed > current_trip['max_speed']:
                        current_trip['max_speed'] = float(speed)
                    
                    # Sum speeds for average (only when moving)
                    if speed and speed > 1:
                        current_trip['speed_sum'] += float(speed)
                        current_trip['speed_count'] += 1
                
                # Trip end: ignition off
                if ignition == 0 and current_trip is not None:
                    # Calculate duration
                    duration_ms = current_trip['end_time'] - current_trip['start_time']
                    
                    # Calculate distance (prefer odometer, fallback to GPS)
                    total_distance = 0
                    if current_trip['end_odometer'] > 0 and current_trip['start_odometer'] > 0:
                        # Use odometer
                        total_distance = current_trip['end_odometer'] - current_trip['start_odometer']
                    else:
                        # Use GPS calculation
                        total_distance = calculate_gps_distance(current_trip['records'])
                    
                    # Calculate average speed
                    avg_speed = 0
                    if current_trip['speed_count'] > 0:
                        avg_speed = current_trip['speed_sum'] / current_trip['speed_count']
                    
                    # Only add trips with reasonable data
                    if duration_ms > 60000:  # At least 1 minute
                        trips.append({
                            'start_time': current_trip['start_time'],
                            'end_time': current_trip['end_time'],
                            'duration_ms': duration_ms,
                            'total_distance': int(total_distance),  # meters
                            'max_speed': round(current_trip['max_speed'], 1),  # km/h
                            'avg_speed': round(avg_speed, 1),  # km/h
                            'start_odometer': current_trip['start_odometer'],
                            'end_odometer': current_trip['end_odometer'],
                            'num_points': len(current_trip['records']),
                            'ongoing': False,
                            'vin': current_trip['vin'],
                            'vehicle_make': current_trip['vehicle_make'],
                            'vehicle_model': current_trip['vehicle_model'],
                            'vehicle_year': current_trip['vehicle_year'],
                            'distance_source': 'odometer' if current_trip['end_odometer'] > 0 else 'gps'
                        })
                    
                    current_trip = None
        
        # Add ongoing trip if exists
        if current_trip is not None:
            duration_ms = current_trip['end_time'] - current_trip['start_time']
            
            # Calculate distance
            total_distance = 0
            if current_trip['end_odometer'] > 0 and current_trip['start_odometer'] > 0:
                total_distance = current_trip['end_odometer'] - current_trip['start_odometer']
            else:
                total_distance = calculate_gps_distance(current_trip['records'])
            
            avg_speed = 0
            if current_trip['speed_count'] > 0:
                avg_speed = current_trip['speed_sum'] / current_trip['speed_count']
            
            trips.append({
                'start_time': current_trip['start_time'],
                'end_time': current_trip['end_time'],
                'duration_ms': duration_ms,
                'total_distance': int(total_distance),
                'max_speed': round(current_trip['max_speed'], 1),
                'avg_speed': round(avg_speed, 1),
                'start_odometer': current_trip['start_odometer'],
                'end_odometer': current_trip['end_odometer'],
                'num_points': len(current_trip['records']),
                'ongoing': True,
                'vin': current_trip['vin'],
                'vehicle_make': current_trip['vehicle_make'],
                'vehicle_model': current_trip['vehicle_model'],
                'vehicle_year': current_trip['vehicle_year'],
                'distance_source': 'odometer' if current_trip['end_odometer'] > 0 else 'gps'
            })
        
        return jsonify({
            'count': len(trips),
            'trips': trips,
            'imei': imei,
            'vin': vin,
            'vehicle': vehicle_info
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)