"""
POPTOP API Server - Connected to New Teltonika Pipeline
Updated: November 14, 2025
Database: Timescale Cloud (replacing DynamoDB)
"""

import json
import psycopg2
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta
import math

app = Flask(__name__)
CORS(app)

# Timescale Connection Pool
timescale_conn = None

def get_timescale_connection():
    """Get or create Timescale connection"""
    global timescale_conn
    if timescale_conn is None or timescale_conn.closed:
        timescale_conn = psycopg2.connect(
            host='pfz4m2fxdm.ubqkw0pnd9.tsdb.cloud.timescale.com',
            port=38416,
            database='tsdb',
            user='tsdbadmin',
            password='u2c06kpgklnlvq6g',
            connect_timeout=10
        )
    return timescale_conn

def parse_raw_json(raw_json_str):
    """Parse the raw_json field from Timescale to extract all 53 IO elements"""
    try:
        if isinstance(raw_json_str, str):
            data = json.loads(raw_json_str)
        else:
            data = raw_json_str
        
        io_elements = data.get('io', {})
        return io_elements
    except:
        return {}

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two GPS points in meters"""
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371000  # Earth radius in meters
    return c * r

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        conn = get_timescale_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        
        return jsonify({
            'status': 'ok',
            'timestamp': datetime.utcnow().isoformat(),
            'database': 'Timescale Cloud',
            'table': 'telemetry'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/devices', methods=['GET'])
def list_devices():
    """List all active devices"""
    try:
        conn = get_timescale_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT imei, vin, 
                   MAX(time) as last_seen
            FROM telemetry
            WHERE time > NOW() - INTERVAL '7 days'
            GROUP BY imei, vin
            ORDER BY last_seen DESC
        """)
        
        devices = []
        for row in cursor.fetchall():
            devices.append({
                'imei': row[0],
                'vin': row[1] if row[1] else 'Unknown',
                'last_seen': row[2].isoformat() if row[2] else None
            })
        
        cursor.close()
        return jsonify({
            'count': len(devices),
            'devices': devices
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/latest', methods=['GET'])
@app.route('/api/latest/<imei>', methods=['GET'])
def get_latest_data(imei=None):
    """Get the most recent telemetry data for a device (or all devices)"""
    try:
        conn = get_timescale_connection()
        cursor = conn.cursor()
        
        # If no IMEI provided, get the most recent from any device
        if not imei:
            cursor.execute("""
                SELECT imei FROM telemetry
                ORDER BY time DESC
                LIMIT 1
            """)
            result = cursor.fetchone()
            if not result:
                return jsonify({'error': 'No data found'}), 404
            imei = result[0]
        
        # Get latest record for this IMEI
        cursor.execute("""
            SELECT 
                time, imei, latitude, longitude, altitude, speed_kmh, heading,
                satellites, external_voltage_mv, internal_voltage_mv, ignition,
                movement, gsm_signal, odometer_m, vin, raw_json
            FROM telemetry
            WHERE imei = %s
            ORDER BY time DESC
            LIMIT 1
        """, (imei,))
        
        row = cursor.fetchone()
        if not row:
            cursor.close()
            return jsonify({'error': 'No data found for this IMEI'}), 404
        
        # Parse all IO elements from raw_json
        io_elements = parse_raw_json(row[15])
        
        # Build comprehensive response with ALL 53 IO elements
        result = {
            'imei': row[1],
            'timestamp': int(row[0].timestamp() * 1000),
            'vin': row[14] if row[14] else 'Unknown',
            'data': {
                'timestamp': int(row[0].timestamp() * 1000),
                'datetime': row[0].isoformat(),
                'priority': 0,
                'gps': {
                    'latitude': float(row[2]) if row[2] else 0,
                    'longitude': float(row[3]) if row[3] else 0,
                    'altitude': int(row[4]) if row[4] else 0,
                    'angle': int(row[6]) if row[6] else 0,
                    'satellites': int(row[7]) if row[7] else 0,
                    'speed_kmh': float(row[5]) if row[5] else 0,
                    'valid': (row[7] or 0) > 0
                },
                'io': {
                    # Core metrics from main table
                    'ignition': {'id': 239, 'value': 1 if row[10] else 0, 'description': 'Ignition'},
                    'movement': {'id': 240, 'value': 1 if row[11] else 0, 'description': 'Movement'},
                    'external_voltage': {'id': 66, 'value': row[8], 'description': 'External Voltage (mV)'},
                    'battery_voltage': {'id': 67, 'value': row[9], 'description': 'Battery Voltage (mV)'},
                    'gsm_signal': {'id': 21, 'value': row[12], 'description': 'GSM Signal Strength'},
                    'total_odometer': {'id': 16, 'value': row[13], 'description': 'Total Odometer (m)'},
                }
            }
        }
        
        # Add ALL additional IO elements from raw_json
        for io_name, io_data in io_elements.items():
            if io_name not in result['data']['io']:
                result['data']['io'][io_name] = io_data
        
        cursor.close()
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/history', methods=['GET'])
@app.route('/api/history/<imei>', methods=['GET'])
def get_history(imei=None):
    """Get historical telemetry data"""
    try:
        hours = int(request.args.get('hours', 24))
        limit = int(request.args.get('limit', 1000))
        
        conn = get_timescale_connection()
        cursor = conn.cursor()
        
        # If no IMEI, get most recent device
        if not imei:
            cursor.execute("SELECT imei FROM telemetry ORDER BY time DESC LIMIT 1")
            result = cursor.fetchone()
            if not result:
                return jsonify({'error': 'No data found'}), 404
            imei = result[0]
        
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        cursor.execute("""
            SELECT 
                time, latitude, longitude, altitude, speed_kmh, heading,
                satellites, external_voltage_mv, internal_voltage_mv, ignition,
                movement, gsm_signal, odometer_m, vin, raw_json
            FROM telemetry
            WHERE imei = %s AND time >= %s
            ORDER BY time DESC
            LIMIT %s
        """, (imei, start_time, limit))
        
        records = []
        for row in cursor.fetchall():
            io_elements = parse_raw_json(row[14])
            
            records.append({
                'timestamp': int(row[0].timestamp() * 1000),
                'datetime': row[0].isoformat(),
                'gps': {
                    'latitude': float(row[1]) if row[1] else 0,
                    'longitude': float(row[2]) if row[2] else 0,
                    'altitude': int(row[3]) if row[3] else 0,
                    'angle': int(row[5]) if row[5] else 0,
                    'satellites': int(row[6]) if row[6] else 0,
                    'speed_kmh': float(row[4]) if row[4] else 0
                },
                'io': {
                    'ignition': {'value': 1 if row[9] else 0},
                    'movement': {'value': 1 if row[10] else 0},
                    'external_voltage': {'value': row[7]},
                    'battery_voltage': {'value': row[8]},
                    'gsm_signal': {'value': row[11]},
                    'total_odometer': {'value': row[12]},
                    **io_elements  # Include all other IO elements
                }
            })
        
        cursor.close()
        return jsonify({
            'imei': imei,
            'count': len(records),
            'records': records
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/trips', methods=['GET'])
@app.route('/api/trips/<imei>', methods=['GET'])
def get_trips(imei=None):
    """Get trip history for a device"""
    try:
        hours = int(request.args.get('hours', 168))  # Default 7 days
        
        conn = get_timescale_connection()
        cursor = conn.cursor()
        
        # If no IMEI, get most recent device
        if not imei:
            cursor.execute("SELECT imei FROM telemetry ORDER BY time DESC LIMIT 1")
            result = cursor.fetchone()
            if not result:
                return jsonify({'error': 'No data found'}), 404
            imei = result[0]
        
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Get all records for trip detection
        cursor.execute("""
            SELECT 
                time, latitude, longitude, speed_kmh, ignition, odometer_m, vin, raw_json
            FROM telemetry
            WHERE imei = %s AND time >= %s
            ORDER BY time ASC
        """, (imei, start_time))
        
        rows = cursor.fetchall()
        
        # Trip detection logic
        trips = []
        current_trip = None
        
        for row in rows:
            timestamp = int(row[0].timestamp() * 1000)
            latitude = float(row[1]) if row[1] else None
            longitude = float(row[2]) if row[2] else None
            speed_kmh = float(row[3]) if row[3] else 0
            ignition = row[4]
            odometer = row[5]
            vin = row[6]
            
            io_elements = parse_raw_json(row[7])
            
            # Trip start: ignition on
            if ignition and current_trip is None and latitude and longitude:
                current_trip = {
                    'start_time': timestamp,
                    'start_location': {'latitude': latitude, 'longitude': longitude},
                    'start_datetime': row[0].isoformat(),
                    'start_odometer': odometer,
                    'max_speed': speed_kmh,
                    'speed_sum': 0,
                    'speed_count': 0,
                    'points': [],
                    'vin': vin if vin else 'Unknown'
                }
            
            # Trip ongoing: collect data
            if current_trip is not None:
                current_trip['points'].append({
                    'timestamp': timestamp,
                    'gps': {
                        'latitude': latitude,
                        'longitude': longitude,
                        'speed_kmh': speed_kmh
                    },
                    'io': io_elements
                })
                current_trip['end_time'] = timestamp
                current_trip['end_datetime'] = row[0].isoformat()
                current_trip['end_location'] = {'latitude': latitude, 'longitude': longitude}
                current_trip['end_odometer'] = odometer
                
                if speed_kmh > current_trip['max_speed']:
                    current_trip['max_speed'] = speed_kmh
                
                if speed_kmh > 1:
                    current_trip['speed_sum'] += speed_kmh
                    current_trip['speed_count'] += 1
            
            # Trip end: ignition off
            if not ignition and current_trip is not None:
                duration_ms = current_trip['end_time'] - current_trip['start_time']
                
                # Calculate distance
                if current_trip['end_odometer'] and current_trip['start_odometer']:
                    distance = current_trip['end_odometer'] - current_trip['start_odometer']
                else:
                    # Calculate from GPS
                    distance = 0
                    for i in range(1, len(current_trip['points'])):
                        prev = current_trip['points'][i-1]
                        curr = current_trip['points'][i]
                        if prev['gps']['latitude'] and curr['gps']['latitude']:
                            distance += haversine_distance(
                                prev['gps']['latitude'], prev['gps']['longitude'],
                                curr['gps']['latitude'], curr['gps']['longitude']
                            )
                
                avg_speed = current_trip['speed_sum'] / current_trip['speed_count'] if current_trip['speed_count'] > 0 else 0
                
                # Only add trips longer than 1 minute
                if duration_ms > 60000:
                    trips.append({
                        'id': len(trips) + 1,
                        'start_time': current_trip['start_time'],
                        'start_datetime': current_trip['start_datetime'],
                        'start_location': current_trip['start_location'],
                        'end_time': current_trip['end_time'],
                        'end_datetime': current_trip['end_datetime'],
                        'end_location': current_trip['end_location'],
                        'duration_ms': duration_ms,
                        'distance': distance / 1000,  # Convert to km
                        'max_speed': round(current_trip['max_speed'], 1),
                        'avg_speed': round(avg_speed, 1),
                        'points': current_trip['points'],
                        'ongoing': False,
                        'vin': current_trip['vin']
                    })
                
                current_trip = None
        
        # Add ongoing trip if exists
        if current_trip is not None:
            duration_ms = current_trip['end_time'] - current_trip['start_time']
            
            if current_trip['end_odometer'] and current_trip['start_odometer']:
                distance = current_trip['end_odometer'] - current_trip['start_odometer']
            else:
                distance = 0
                for i in range(1, len(current_trip['points'])):
                    prev = current_trip['points'][i-1]
                    curr = current_trip['points'][i]
                    if prev['gps']['latitude'] and curr['gps']['latitude']:
                        distance += haversine_distance(
                            prev['gps']['latitude'], prev['gps']['longitude'],
                            curr['gps']['latitude'], curr['gps']['longitude']
                        )
            
            avg_speed = current_trip['speed_sum'] / current_trip['speed_count'] if current_trip['speed_count'] > 0 else 0
            
            trips.append({
                'id': len(trips) + 1,
                'start_time': current_trip['start_time'],
                'start_datetime': current_trip['start_datetime'],
                'start_location': current_trip['start_location'],
                'end_time': current_trip['end_time'],
                'end_datetime': current_trip.get('end_datetime', current_trip['start_datetime']),
                'end_location': current_trip.get('end_location', current_trip['start_location']),
                'duration_ms': duration_ms,
                'distance': distance / 1000,
                'max_speed': round(current_trip['max_speed'], 1),
                'avg_speed': round(avg_speed, 1),
                'points': current_trip['points'],
                'ongoing': True,
                'vin': current_trip['vin']
            })
        
        cursor.close()
        return jsonify({
            'imei': imei,
            'count': len(trips),
            'trips': trips
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
@app.route('/api/stats/<imei>', methods=['GET'])
def get_stats(imei=None):
    """Get statistics for a device"""
    try:
        hours = int(request.args.get('hours', 168))
        
        conn = get_timescale_connection()
        cursor = conn.cursor()
        
        # If no IMEI, get most recent device
        if not imei:
            cursor.execute("SELECT imei FROM telemetry ORDER BY time DESC LIMIT 1")
            result = cursor.fetchone()
            if not result:
                return jsonify({'error': 'No data found'}), 404
            imei = result[0]
        
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                MAX(speed_kmh) as max_speed,
                MAX(odometer_m) - MIN(odometer_m) as distance_m,
                MIN(time) as first_seen,
                MAX(time) as last_seen
            FROM telemetry
            WHERE imei = %s AND time >= %s
        """, (imei, start_time))
        
        row = cursor.fetchone()
        
        stats = {
            'imei': imei,
            'period_hours': hours,
            'total_records': int(row[0]) if row[0] else 0,
            'max_speed_kmh': float(row[1]) if row[1] else 0,
            'total_distance_km': float(row[2]) / 1000 if row[2] else 0,
            'first_seen': row[3].isoformat() if row[3] else None,
            'last_seen': row[4].isoformat() if row[4] else None
        }
        
        cursor.close()
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    print(f"""
    ╔═══════════════════════════════════════════════════════════════╗
    ║  POPTOP API Server - Connected to Teltonika Pipeline        ║
    ║  Database: Timescale Cloud                                   ║
    ║  Port: {port}                                                     ║
    ║  Status: Ready to receive requests                           ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    app.run(host='0.0.0.0', port=port, debug=True)
