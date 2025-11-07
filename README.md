# Teltonika Vehicle Tracker Dashboard

A real-time vehicle tracking dashboard for Teltonika FMM00A devices with trip analysis and visualization.

## 🎯 Features

- **Real-time Location Tracking** - View current vehicle position on an interactive map
- **Trip Analysis** - Automatically detect and analyze trips based on ignition cycles
- **Historical Data** - Browse past trips with detailed statistics
- **Live Telemetry** - Monitor speed, voltage, GPS quality, and more
- **Auto-refresh** - Dashboard updates automatically every 5 seconds
- **Responsive Design** - Works on desktop and mobile devices

## 📋 Architecture

```
Teltonika FMM00A Device
        ↓
Soracom Funnel (via TCP)
        ↓
AWS IoT Core
        ↓
Lambda Function (Decoder)
        ↓
DynamoDB Storage
        ↓
Flask API Server
        ↓
React Dashboard (HTML)
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- AWS credentials configured (for DynamoDB access)
- Teltonika FMM00A device configured with Soracom
- DynamoDB table: `teltonika-events`

### Installation

1. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

2. **Configure AWS credentials:**
```bash
aws configure
# Enter your AWS Access Key ID, Secret Access Key, and Region (us-west-1)
```

3. **Start the API server:**
```bash
python api_server.py
```

The server will start on `http://localhost:5000`

4. **Open the dashboard:**
```bash
# Simply open dashboard.html in your web browser
# Or use a local web server:
python -m http.server 8000
# Then visit http://localhost:8000/dashboard.html
```

## 📁 File Structure

```
teltonika-tracker/
├── lambda_function_final.py    # AWS Lambda decoder (already deployed)
├── api_server.py               # Flask API backend
├── dashboard.html              # React dashboard frontend
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## 🔧 Configuration

### API Server

Edit `api_server.py` to change:
- DynamoDB table name (default: `teltonika-events`)
- AWS region (default: `us-west-1`)
- Server port (default: `5000`)

### Dashboard

Edit `dashboard.html` line ~17 to change:
```javascript
const API_BASE_URL = 'http://localhost:5000/api';
```

Change `localhost:5000` to your API server address if running on a different machine.

### Default IMEI

Change the default device IMEI in `dashboard.html` line ~18:
```javascript
const DEFAULT_IMEI = '862464068525406';
```

## 🌐 API Endpoints

### `GET /api/health`
Health check endpoint
```json
{
  "status": "ok",
  "timestamp": "2025-11-07T..."
}
```

### `GET /api/latest?imei=<IMEI>`
Get the latest data point for a device
```json
{
  "imei": "862464068525406",
  "timestamp": 1762497279796,
  "data": {
    "timestamp": 1762497278000,
    "datetime": "2025-11-07T06:34:38",
    "gps": { ... },
    "io": { ... }
  }
}
```

### `GET /api/history?imei=<IMEI>&hours=24`
Get historical data points
```json
{
  "imei": "862464068525406",
  "count": 150,
  "records": [ ... ]
}
```

### `GET /api/trips?imei=<IMEI>&hours=168`
Get trip data (grouped by ignition cycles)
```json
{
  "imei": "862464068525406",
  "count": 5,
  "trips": [
    {
      "id": 1,
      "start_time": 1762497279796,
      "end_time": 1762497379796,
      "distance": 12.5,
      "max_speed": 65.3,
      "avg_speed": 42.1,
      "duration_ms": 100000,
      "points": [ ... ]
    }
  ]
}
```

### `GET /api/stats?imei=<IMEI>&hours=168`
Get statistics for a time period
```json
{
  "imei": "862464068525406",
  "period_hours": 168,
  "total_records": 1234,
  "total_distance_km": 145.6,
  "max_speed_kmh": 95.2
}
```

## 📊 Dashboard Features

### Main View
- Interactive map showing current vehicle location
- Real-time telemetry cards (speed, ignition, GPS, voltage, etc.)
- Auto-refresh toggle
- Manual refresh button

### Trip Analysis
- Automatic trip detection based on ignition on/off cycles
- Click any trip in the history to view on the map
- Trip details: duration, distance, max/avg speed
- Route visualization with start (green) and end (red) markers

### Data Display
- Speed (km/h)
- Ignition status (ON/OFF)
- GPS satellite count
- GSM signal strength
- External voltage (vehicle battery)
- Internal battery voltage
- Altitude
- Total odometer reading

## 🚗 Using with Your Vehicle

### Current Setup (Desk Testing)
The device is currently powered on your desk and sending test data.

### When Installing in Vehicle:

1. **Mount the device** in your vehicle
2. **Connect to vehicle power:**
   - Red wire → Vehicle battery positive (+12V)
   - Black wire → Vehicle ground/negative
   - Connect to a switched power source if you want ignition detection

3. **Test ignition detection:**
   - Start your engine
   - Check dashboard - ignition should show "ON"
   - Drive around the block
   - Turn off engine - new trip should appear in history

4. **Go for a drive!**
   - The dashboard will track your route in real-time
   - Each ignition cycle creates a new trip
   - All data is automatically stored in DynamoDB

## 🔍 Troubleshooting

### Dashboard shows "Connection Error"
- Make sure `api_server.py` is running
- Check that the API_BASE_URL in `dashboard.html` is correct
- Verify firewall isn't blocking port 5000

### No data appearing
- Check that your Teltonika device is sending data
- Verify Lambda function is running in AWS
- Check DynamoDB table has data: `aws dynamodb scan --table-name teltonika-events --limit 1`

### Trips not appearing
- Make sure ignition wire is connected properly
- Check that IO element 239 (ignition) is changing between 0 and 1
- View raw data in DynamoDB to verify ignition values

### Map not loading
- Check browser console for errors
- Verify internet connection (map tiles load from OpenStreetMap)
- Try refreshing the page

## 🎨 Customization

### Change Map Style
Edit `dashboard.html` around line 80 to use different map tiles:
```javascript
// Current: OpenStreetMap
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png')

// Alternative: Satellite view (requires MapBox API key)
L.tileLayer('https://api.mapbox.com/styles/v1/mapbox/satellite-v9/tiles/{z}/{x}/{y}?access_token=YOUR_TOKEN')
```

### Add More Telemetry
Edit the dashboard's current status section to add more IO elements from your device.

### Export Trip Data
Add export functionality to download trips as CSV/JSON for analysis in Excel or other tools.

## 📝 Data Schema

### DynamoDB Item Structure
```json
{
  "imei": "862464068525406",
  "timestamp": 1762497279796,
  "imsi": "295050916914927",
  "operatorId": "OP0055020544",
  "num_records": 1,
  "payload_length": 85,
  "records": "[{...}]",
  "raw_payload": "AAAAAAAAAEkIAQ...",
  "received_at": 1762497280732
}
```

## 🔐 Security Considerations

### Production Deployment:
1. **Use HTTPS** for both API and dashboard
2. **Add authentication** to API endpoints
3. **Restrict CORS** to specific origins
4. **Use environment variables** for sensitive config
5. **Set up IAM roles** properly for Lambda/DynamoDB access
6. **Enable DynamoDB encryption** at rest
7. **Use API Gateway** instead of direct Flask server
8. **Add rate limiting** to prevent abuse

## 📈 Future Enhancements

- [ ] Export trips to CSV/Excel
- [ ] Geofencing alerts
- [ ] Speed limit warnings
- [ ] Maintenance reminders based on odometer
- [ ] Multiple vehicle support
- [ ] Mobile app version
- [ ] Push notifications
- [ ] Driver behavior scoring
- [ ] Fuel efficiency calculations
- [ ] Route playback with timeline scrubber

## 🆘 Support

For issues or questions:
1. Check CloudWatch Logs for Lambda function errors
2. Check DynamoDB for data issues
3. Check browser console for dashboard errors
4. Verify Soracom Funnel is receiving data from device

## 📄 License

This project is for personal use. Teltonika is a trademark of UAB Teltonika Telematics.

---

**Happy Tracking! 🚗💨**
