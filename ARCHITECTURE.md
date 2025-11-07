# System Architecture

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        TELTONIKA FMM00A                             │
│  • GPS Tracking                                                     │
│  • Ignition Detection                                               │
│  • Vehicle Telemetry                                                │
│  • IMEI: 862464068525406                                            │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         │ Binary Data (Codec 8)
                         │ via TCP Protocol
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      SORACOM FUNNEL                                 │
│  • IoT Connectivity                                                 │
│  • Protocol Translation                                             │
│  • Data Forwarding                                                  │
│  • sendPayloadsAsBinary: false (Base64 encoding)                    │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         │ JSON with Base64 Payload
                         │ MQTT Topic: teltonika/data
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      AWS IoT CORE                                   │
│  • Message Broker                                                   │
│  • IoT Rule: process_teltonika_data                                 │
│  • SQL: SELECT * FROM 'teltonika/data'                              │
│  • Actions: Republish + Lambda                                      │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         │ Event Trigger
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   AWS LAMBDA FUNCTION                               │
│  Function: lambda_function_final.py                                 │
│  • Base64 Decode                                                    │
│  • Parse Teltonika Binary Protocol                                  │
│  • Extract GPS, IO Elements                                         │
│  • Structure Data                                                   │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         │ Parsed JSON
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       DYNAMODB                                      │
│  Table: teltonika-events                                            │
│  • Primary Key: imei (String)                                       │
│  • Sort Key: timestamp (Number)                                     │
│  • Attributes: gps, io, parsed_data, etc.                           │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         │ Query/Scan
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    FLASK API SERVER                                 │
│  File: api_server.py                                                │
│  Port: 5000                                                         │
│  Endpoints:                                                         │
│  • GET /api/latest     - Latest data point                          │
│  • GET /api/history    - Historical records                         │
│  • GET /api/trips      - Trip analysis                              │
│  • GET /api/stats      - Statistics                                 │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         │ REST API (JSON)
                         │ CORS Enabled
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    REACT DASHBOARD                                  │
│  File: dashboard.html                                               │
│  • Interactive Leaflet Map                                          │
│  • Real-time Telemetry Cards                                        │
│  • Trip History List                                                │
│  • Auto-refresh (5s)                                                │
│  • Trip Route Visualization                                         │
└─────────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Teltonika FMM00A Device
**Purpose:** GPS tracker with vehicle telemetry
**Protocol:** Codec 8 (binary)
**Connection:** Soracom SIM card (IMSI: 295050916914927)
**Data Frequency:** Configurable (currently real-time when moving)

**Transmitted Data:**
- GPS coordinates (latitude, longitude, altitude)
- Speed and heading
- Ignition status (IO 239)
- External voltage (IO 66) - Vehicle battery
- Internal battery voltage (IO 67)
- GSM signal strength (IO 21)
- Odometer readings (IO 16, 199)
- Movement sensor (IO 240)

### 2. Soracom Funnel
**Purpose:** IoT connectivity and protocol bridge
**Configuration:**
- Provider: AWS
- Service: AWS IoT
- Resource: a3sq7y5xkh0u57-ats.iot.us-west-1.amazonaws.com
- Topic: teltonika/data
- Payload Format: Base64 (sendPayloadsAsBinary: false)

**Function:**
- Receives binary TCP data from device
- Encodes payload as Base64
- Wraps in JSON with metadata (IMEI, IMSI, timestamp)
- Publishes to AWS IoT Core

### 3. AWS IoT Core
**Purpose:** Message routing and processing
**Rule:** process_teltonika_data
- SQL: `SELECT * FROM 'teltonika/data'`
- Action 1: Republish to topic (for debugging)
- Action 2: Trigger Lambda function

### 4. AWS Lambda Function
**Purpose:** Decode binary telemetry protocol
**Runtime:** Python 3.x
**Key Functions:**
```python
parse_teltonika_packet()  # Main parser
parse_avl_record()        # Individual record parser
get_io_info()             # IO element mapping
```

**Processing Steps:**
1. Extract Base64 payload from event
2. Decode Base64 → binary
3. Parse packet structure:
   - Preamble (4 bytes)
   - Data length (4 bytes)
   - Codec ID (1 byte)
   - Number of records (1 byte)
   - AVL records (variable)
   - CRC (4 bytes)
4. Extract GPS and IO elements
5. Store in DynamoDB

### 5. DynamoDB Table
**Purpose:** Persistent storage
**Schema:**
```
Primary Key: imei (String)
Sort Key: timestamp (Number)

Attributes:
- imsi: String
- operatorId: String
- num_records: Number
- payload_length: Number
- records: String (JSON)
- latitude: Number (for quick queries)
- longitude: Number (for quick queries)
- speed: Number
- codec_id: Number
- received_at: Number
- raw_payload_sample: String
```

### 6. Flask API Server
**Purpose:** REST API for dashboard
**Endpoints:**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| /api/health | GET | Health check |
| /api/latest | GET | Latest device data |
| /api/history | GET | Historical records |
| /api/trips | GET | Trip analysis |
| /api/stats | GET | Statistics |

**Features:**
- CORS enabled for browser access
- Decimal → Float conversion
- Trip detection algorithm
- Distance calculation
- Query optimization

### 7. React Dashboard
**Purpose:** User interface
**Technology:** React 18 + Leaflet.js + Tailwind CSS

**Features:**
- Interactive OpenStreetMap
- Real-time location marker
- Trip route visualization
- Telemetry cards (speed, ignition, GPS, voltage)
- Trip history sidebar
- Auto-refresh toggle
- Click-to-view trip details

**Update Cycle:**
```
User opens page
    ↓
Load data from API
    ↓
Display on map
    ↓
Wait 5 seconds (if auto-refresh)
    ↓
Fetch latest data
    ↓
Update display
    ↓
Repeat
```

## Data Structures

### Raw Device Packet (Binary)
```
[Preamble][Data Length][Codec][Records][Records Check][CRC]
    4B        4B          1B     Var         1B         4B
```

### AVL Record Structure
```
[Timestamp][Priority][GPS Element][IO Element]
    8B         1B         15B          Var
```

### API Response (Latest)
```json
{
  "imei": "862464068525406",
  "timestamp": 1762497279796,
  "data": {
    "timestamp": 1762497278000,
    "datetime": "2025-11-07T06:34:38",
    "priority": 0,
    "gps": {
      "latitude": 38.54963,
      "longitude": -121.4792916,
      "altitude": 8,
      "angle": 155,
      "satellites": 7,
      "speed_kmh": 0
    },
    "io": {
      "ignition": { "id": 239, "value": 1 },
      "movement": { "id": 240, "value": 0 },
      "external_voltage": { "id": 66, "value": 13857 },
      ...
    }
  }
}
```

### Trip Object
```json
{
  "id": 1,
  "start_time": 1762497279796,
  "end_time": 1762497379796,
  "start_location": { "latitude": 38.54963, "longitude": -121.4792916 },
  "end_location": { "latitude": 38.55963, "longitude": -121.4892916 },
  "duration_ms": 100000,
  "distance": 12.5,
  "max_speed": 65.3,
  "avg_speed": 42.1,
  "points": [ ... ],
  "ongoing": false
}
```

## Performance Characteristics

- **Device Update Frequency:** 1-30 seconds (configurable)
- **Lambda Execution:** < 1 second
- **DynamoDB Write:** < 100ms
- **API Response Time:** 200-500ms
- **Dashboard Refresh:** 5 seconds (configurable)
- **Map Render Time:** < 1 second

## Security Considerations

**Current Implementation (Development):**
- ⚠️ No authentication on API
- ⚠️ CORS open to all origins
- ⚠️ HTTP only (no HTTPS)
- ✅ AWS credentials secured via IAM

**Production Requirements:**
- [ ] Add API authentication (JWT/OAuth)
- [ ] Restrict CORS to specific domain
- [ ] Enable HTTPS/TLS
- [ ] Use API Gateway with rate limiting
- [ ] Enable DynamoDB encryption
- [ ] Use AWS Secrets Manager for credentials
- [ ] Add IP whitelisting
- [ ] Implement request signing

## Scalability

**Current Capacity:**
- Single device: ✅ Supported
- Multiple devices: ✅ Supported (filter by IMEI)
- High frequency updates: ✅ Supported (DynamoDB scales)
- Concurrent users: ⚠️ Limited by Flask (use Gunicorn for production)

**Production Recommendations:**
- Use AWS API Gateway instead of Flask
- Enable DynamoDB Auto Scaling
- Add CloudFront CDN for dashboard
- Implement data archival (S3 for old data)
- Add Redis cache for frequently accessed data

## Monitoring & Debugging

**CloudWatch Logs:**
- Lambda function logs: `/aws/lambda/function-name`
- IoT Core logs: IoT Core console
- API server: Terminal/systemd logs

**Debugging Tools:**
- AWS IoT Test Client: View MQTT messages
- DynamoDB Console: Query raw data
- Browser Console: Dashboard JavaScript errors
- Postman: Test API endpoints

**Key Metrics to Monitor:**
- Lambda invocations per minute
- Lambda error rate
- DynamoDB read/write capacity
- API response times
- Dashboard load times
- Device connection status

## Cost Estimation

**Monthly Costs (Single Device, 24/7 tracking):**
- Soracom SIM: ~$10-20/month
- AWS IoT Core: ~$5/month
- Lambda: < $1/month (free tier)
- DynamoDB: ~$2-5/month
- Data Transfer: < $1/month
- **Total: ~$18-27/month**

**Cost Optimization:**
- Reduce device update frequency when stationary
- Use DynamoDB on-demand pricing
- Archive old data to S3
- Use Lambda reserved concurrency
