import json
import base64
import struct
import boto3
from datetime import datetime

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('teltonika-events')

def lambda_handler(event, context):
    """
    Parse Teltonika data from Soracom Funnel via AWS IoT Core
    
    Expected event structure from Soracom Funnel:
    {
        "credentialsId": "...",
        "operatorId": "...",
        "destination": {...},
        "sourceProtocol": "tcp",
        "timestamp": 1234567890,
        "imsi": "...",
        "imei": "..."
    }
    
    The base64 payload appears to be in the long string in sourceProtocol
    or possibly in a field that wasn't visible in the screenshot
    """
    try:
        # Log the complete event for debugging
        print("="*80)
        print("RECEIVED EVENT:")
        print(json.dumps(event, indent=2, default=str))
        print("="*80)
        
        # Extract metadata
        imei = event.get('imei', '')
        imsi = event.get('imsi', '')
        operator_id = event.get('operatorId', '')
        event_timestamp = event.get('timestamp', 0)
        source_protocol = event.get('sourceProtocol', '')
        
        print(f"Metadata - IMEI: {imei}, IMSI: {imsi}, Operator: {operator_id}")
        print(f"Source Protocol: {source_protocol}")
        print(f"Timestamp: {event_timestamp}")
        
        # Find the base64 payload
        # Based on Soracom documentation and the screenshot, the payload could be in:
        payload_b64 = None
        payload_source = None
        
        # Check all possible locations
        possible_locations = [
            ('sourceProtocol', event.get('sourceProtocol')),
            ('payload', event.get('payload')),
            ('payloads', event.get('payloads')),
            ('data', event.get('data')),
        ]
        
        # Also check nested in destination
        if 'destination' in event and isinstance(event['destination'], dict):
            dest = event['destination']
            possible_locations.extend([
                ('destination.payload', dest.get('payload')),
                ('destination.data', dest.get('data')),
            ])
        
        # Find the payload by looking for base64-like strings
        for location, value in possible_locations:
            if value and isinstance(value, str):
                # sourceProtocol is usually just "tcp", so skip if it's that short
                if location == 'sourceProtocol' and len(value) < 20:
                    continue
                    
                # Try to decode as base64
                try:
                    test_decode = base64.b64decode(value)
                    if len(test_decode) > 8:  # Should be at least a few bytes
                        payload_b64 = value
                        payload_source = location
                        print(f"Found payload in: {location}")
                        print(f"Payload length (base64): {len(value)} chars")
                        break
                except:
                    continue
        
        # If still not found, look through ALL string fields
        if not payload_b64:
            print("Searching all event fields for base64 data...")
            for key, value in event.items():
                if isinstance(value, str) and len(value) > 100:
                    try:
                        test_decode = base64.b64decode(value)
                        if len(test_decode) > 8:
                            payload_b64 = value
                            payload_source = key
                            print(f"Found payload in unexpected location: {key}")
                            break
                    except:
                        continue
        
        if not payload_b64:
            error_msg = f"No base64 payload found. Available fields: {list(event.keys())}"
            print(error_msg)
            
            # Log the first 200 chars of each string field for debugging
            for key, value in event.items():
                if isinstance(value, str):
                    print(f"{key}: {value[:200]}")
            
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'No payload found',
                    'event_keys': list(event.keys()),
                    'event_sample': str(event)[:500]
                })
            }
        
        # Decode base64 to binary
        try:
            payload_binary = base64.b64decode(payload_b64)
            print(f"Successfully decoded payload from {payload_source}")
            print(f"Binary length: {len(payload_binary)} bytes")
            
            # Print first 20 bytes in hex for verification
            hex_preview = ' '.join([f'{b:02x}' for b in payload_binary[:20]])
            print(f"First 20 bytes (hex): {hex_preview}")
            
        except Exception as e:
            print(f"Error decoding base64: {str(e)}")
            return {
                'statusCode': 400,
                'body': json.dumps(f'Base64 decode error: {str(e)}')
            }
        
        # Parse Teltonika Codec 8 format
        parsed_data = parse_teltonika_packet(payload_binary)
        
        if not parsed_data.get('records'):
            print("WARNING: No records parsed from payload")
        else:
            print(f"Successfully parsed {len(parsed_data['records'])} record(s)")
        
        # Add metadata to parsed data
        parsed_data['imei'] = imei
        parsed_data['imsi'] = imsi
        parsed_data['operatorId'] = operator_id
        parsed_data['event_timestamp'] = event_timestamp
        parsed_data['received_at'] = int(datetime.now().timestamp() * 1000)
        parsed_data['payload_source'] = payload_source
        
        # Store in DynamoDB
        try:
            item = {
                'imei': imei if imei else 'unknown',
                'timestamp': event_timestamp if event_timestamp else int(datetime.now().timestamp() * 1000),
                'imsi': imsi,
                'operatorId': operator_id,
                'payload_length': len(payload_binary),
                'num_records': len(parsed_data.get('records', [])),
                'codec_id': parsed_data.get('codec_id', 0),
                'received_at': parsed_data['received_at']
            }
            
            # Add parsed records if available
            if parsed_data.get('records'):
                item['records'] = json.dumps(parsed_data['records'])
                # Add latest GPS coordinates for easy querying
                latest_record = parsed_data['records'][-1]
                if 'gps' in latest_record:
                    item['latitude'] = latest_record['gps'].get('latitude', 0)
                    item['longitude'] = latest_record['gps'].get('longitude', 0)
                    item['speed'] = latest_record['gps'].get('speed_kmh', 0)
            
            # Store truncated raw payload for debugging
            item['raw_payload_sample'] = payload_b64[:200]
            
            table.put_item(Item=item)
            print(f"Successfully stored data in DynamoDB for IMEI {imei}")
            
        except Exception as e:
            print(f"Error storing in DynamoDB: {str(e)}")
            import traceback
            traceback.print_exc()
            # Don't fail the Lambda if DynamoDB write fails
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Success',
                'records_parsed': len(parsed_data.get('records', [])),
                'imei': imei,
                'payload_source': payload_source
            })
        }
        
    except Exception as e:
        error_msg = f"Error parsing Teltonika data: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'type': type(e).__name__
            })
        }

def parse_teltonika_packet(data):
    """
    Parse complete Teltonika TCP packet (Codec 8 or 8E)
    
    Packet structure:
    - Preamble: 4 bytes (0x00000000)
    - Data Length: 4 bytes
    - Codec ID: 1 byte (0x08 for Codec 8, 0x8E for Codec 8E)
    - Number of Records: 1 byte
    - Records: Variable
    - Number of Records (again): 1 byte
    - CRC: 4 bytes
    """
    result = {'records': []}
    
    try:
        if len(data) < 10:
            raise Exception(f"Packet too short: {len(data)} bytes (minimum 10 required)")
        
        offset = 0
        
        # Print hex dump of first 20 bytes for debugging
        hex_dump = ' '.join([f'{b:02x}' for b in data[:min(20, len(data))]])
        print(f"Packet hex (first 20 bytes): {hex_dump}")
        
        # Preamble (4 bytes) - usually 0x00000000
        preamble = struct.unpack('>I', data[offset:offset+4])[0]
        print(f"Preamble: 0x{preamble:08x}")
        offset += 4
        
        # Data field length (4 bytes)
        data_length = struct.unpack('>I', data[offset:offset+4])[0]
        print(f"Data length field: {data_length} bytes")
        offset += 4
        
        if data_length > len(data) - 8:  # -8 for preamble and data length
            print(f"WARNING: Data length ({data_length}) exceeds packet size")
        
        # Codec ID (1 byte)
        codec_id = data[offset]
        codec_name = {0x08: 'Codec 8', 0x8E: 'Codec 8E', 0x10: 'Codec 16'}.get(codec_id, f'Unknown (0x{codec_id:02x})')
        print(f"Codec ID: 0x{codec_id:02x} ({codec_name})")
        offset += 1
        
        result['codec_id'] = codec_id
        result['codec_name'] = codec_name
        
        # Number of records (1 byte)
        num_records = data[offset]
        print(f"Number of records: {num_records}")
        offset += 1
        
        result['num_records'] = num_records
        
        if num_records == 0:
            print("No records to parse")
            return result
        
        # Parse each AVL record
        for i in range(num_records):
            try:
                print(f"\nParsing record {i+1}/{num_records} starting at offset {offset}")
                record, offset = parse_avl_record(data, offset, codec_id)
                result['records'].append(record)
                print(f"Record {i+1} parsed successfully, new offset: {offset}")
            except Exception as e:
                print(f"Error parsing record {i+1}: {str(e)}")
                import traceback
                traceback.print_exc()
                # Continue to next record or stop
                break
        
        # Verify number of records (should match)
        if offset < len(data):
            num_records_check = data[offset]
            offset += 1
            print(f"Number of records (check): {num_records_check}")
            if num_records_check != num_records:
                print(f"WARNING: Record count mismatch! Header: {num_records}, Footer: {num_records_check}")
        
        # CRC-16 (4 bytes)
        if offset + 4 <= len(data):
            crc = struct.unpack('>I', data[offset:offset+4])[0]
            print(f"CRC-16: 0x{crc:08x}")
            result['crc'] = crc
        
        return result
        
    except Exception as e:
        print(f"Error in parse_teltonika_packet: {str(e)}")
        import traceback
        traceback.print_exc()
        return result

def parse_avl_record(data, offset, codec_id):
    """
    Parse a single AVL record
    
    Record structure:
    - Timestamp: 8 bytes (milliseconds since 1970-01-01 UTC)
    - Priority: 1 byte
    - GPS Element: 15 bytes
    - IO Element: Variable
    """
    record = {}
    start_offset = offset
    
    try:
        # Timestamp (8 bytes)
        if offset + 8 > len(data):
            raise Exception(f"Not enough data for timestamp at offset {offset}")
        
        timestamp_ms = struct.unpack('>Q', data[offset:offset+8])[0]
        record['timestamp'] = timestamp_ms
        record['datetime'] = format_timestamp(timestamp_ms)
        offset += 8
        
        # Priority (1 byte): 0=Low, 1=High, 2=Panic
        priority = data[offset]
        record['priority'] = priority
        offset += 1
        
        # === GPS Element (15 bytes) ===
        
        # Longitude (4 bytes, signed, divide by 10,000,000)
        longitude_raw = struct.unpack('>i', data[offset:offset+4])[0]
        longitude = longitude_raw / 10000000.0
        offset += 4
        
        # Latitude (4 bytes, signed, divide by 10,000,000)
        latitude_raw = struct.unpack('>i', data[offset:offset+4])[0]
        latitude = latitude_raw / 10000000.0
        offset += 4
        
        # Altitude (2 bytes, signed, meters)
        altitude = struct.unpack('>h', data[offset:offset+2])[0]
        offset += 2
        
        # Angle (2 bytes, unsigned, degrees from north)
        angle = struct.unpack('>H', data[offset:offset+2])[0]
        offset += 2
        
        # Satellites (1 byte)
        satellites = data[offset]
        offset += 1
        
        # Speed (2 bytes, unsigned, km/h)
        speed = struct.unpack('>H', data[offset:offset+2])[0]
        offset += 2
        
        record['gps'] = {
            'latitude': latitude,
            'longitude': longitude,
            'altitude': altitude,
            'angle': angle,
            'satellites': satellites,
            'speed_kmh': speed,
            'valid': satellites > 0 and latitude != 0 and longitude != 0
        }
        
        # === IO Element ===
        
        # Event IO ID (1 byte) - which IO element triggered this record
        event_io_id = data[offset]
        offset += 1
        
        # Total number of IO elements (1 byte)
        total_io = data[offset]
        offset += 1
        
        record['event_io_id'] = event_io_id
        record['total_io_elements'] = total_io
        record['io'] = {}
        
        # Parse IO elements by size
        # Codec 8: 1, 2, 4, 8 byte IOs
        # Codec 8E: 1, 2, 4, 8 byte IOs + variable length
        
        io_sizes = [1, 2, 4, 8]
        if codec_id == 0x8E:
            io_sizes.append('X')  # Variable length
        
        for io_size in io_sizes:
            if offset >= len(data):
                break
            
            # Number of IO elements of this size
            num_io_elements = data[offset]
            offset += 1
            
            if num_io_elements == 0:
                continue
            
            for j in range(num_io_elements):
                if offset >= len(data):
                    break
                
                # IO ID (1 byte for Codec 8, 2 bytes for Codec 8E)
                if codec_id == 0x8E:
                    if offset + 2 > len(data):
                        break
                    io_id = struct.unpack('>H', data[offset:offset+2])[0]
                    offset += 2
                else:
                    io_id = data[offset]
                    offset += 1
                
                # Read IO value based on size
                if io_size == 'X':
                    # Variable length - first 2 bytes indicate length
                    if offset + 2 > len(data):
                        break
                    io_value_length = struct.unpack('>H', data[offset:offset+2])[0]
                    offset += 2
                    
                    if offset + io_value_length > len(data):
                        break
                    
                    # Store as hex string
                    io_value = data[offset:offset+io_value_length].hex()
                    offset += io_value_length
                    
                elif io_size == 1:
                    io_value = data[offset]
                    offset += 1
                elif io_size == 2:
                    io_value = struct.unpack('>H', data[offset:offset+2])[0]
                    offset += 2
                elif io_size == 4:
                    io_value = struct.unpack('>I', data[offset:offset+4])[0]
                    offset += 4
                elif io_size == 8:
                    io_value = struct.unpack('>Q', data[offset:offset+8])[0]
                    offset += 8
                
                # Get friendly name for IO element
                io_info = get_io_info(io_id)
                record['io'][io_info['name']] = {
                    'id': io_id,
                    'value': io_value,
                    'description': io_info['description']
                }
        
        bytes_parsed = offset - start_offset
        print(f"  Parsed {bytes_parsed} bytes, GPS: ({latitude:.6f}, {longitude:.6f}), IO elements: {len(record['io'])}")
        
        return record, offset
        
    except Exception as e:
        print(f"Error in parse_avl_record at offset {offset}: {str(e)}")
        raise

def format_timestamp(timestamp_ms):
    """Convert milliseconds since epoch to ISO datetime"""
    try:
        return datetime.fromtimestamp(timestamp_ms / 1000).isoformat()
    except:
        return f"invalid_{timestamp_ms}"

def get_io_info(io_id):
    """
    Get information about Teltonika IO elements
    FMM00A specific
    """
    io_database = {
        # Digital inputs
        1: ('digital_input_1', 'Digital Input 1'),
        2: ('digital_input_2', 'Digital Input 2'),
        3: ('digital_input_3', 'Digital Input 3'),
        4: ('digital_input_4', 'Digital Input 4'),
        
        # Analog inputs
        9: ('analog_input_1', 'Analog Input 1 (mV)'),
        10: ('analog_input_2', 'Analog Input 2 (mV)'),
        11: ('ibutton_id', 'iButton ID'),
        
        # System
        16: ('total_odometer', 'Total Odometer (m)'),
        21: ('gsm_signal', 'GSM Signal Strength'),
        24: ('speed', 'Speed (km/h)'),
        66: ('external_voltage', 'External Voltage (mV)'),
        67: ('battery_voltage', 'Battery Voltage (mV)'),
        68: ('battery_current', 'Battery Current (mA)'),
        69: ('gnss_status', 'GNSS Status'),
        80: ('data_mode', 'Data Mode'),
        113: ('battery_level', 'Battery Level (%)'),
        181: ('gnss_pdop', 'GNSS PDOP'),
        182: ('gnss_hdop', 'GNSS HDOP'),
        199: ('trip_odometer', 'Trip Odometer (m)'),
        
        # Status flags
        239: ('ignition', 'Ignition'),
        240: ('movement', 'Movement'),
        241: ('active_gsm_operator', 'Active GSM Operator'),
        
        # Dallas temperature sensors
        72: ('dallas_temp_1', 'Dallas Temperature 1 (°C)'),
        73: ('dallas_temp_2', 'Dallas Temperature 2 (°C)'),
        74: ('dallas_temp_3', 'Dallas Temperature 3 (°C)'),
        75: ('dallas_temp_4', 'Dallas Temperature 4 (°C)'),
        
        # Additional
        200: ('sleep_mode', 'Sleep Mode'),
        205: ('cell_id', 'Cell ID'),
        206: ('area_code', 'Area Code (LAC)'),
        247: ('crash_detection', 'Crash Detection'),
    }
    
    if io_id in io_database:
        name, description = io_database[io_id]
    else:
        name = f'io_{io_id}'
        description = f'Unknown IO Element {io_id}'
    
    return {'name': name, 'description': description}
