# 🚗 Teltonika Tracker Dashboard - Quick Start

## What You've Built

A complete vehicle tracking system with:
- ✅ Real-time GPS tracking
- ✅ Trip analysis (detects ignition on/off)
- ✅ Historical data visualization
- ✅ Live telemetry monitoring
- ✅ Interactive map display

## Current Status

Your Teltonika FMM00A device is working! Here's the latest data:
- **IMEI:** 862464068525406
- **Location:** Sacramento, CA (38.54963°N, 121.4792°W)
- **Status:** Device on desk, not in vehicle yet
- **Data Flow:** Device → Soracom → AWS IoT → Lambda → DynamoDB ✅

## 🚀 How to Run the Dashboard

### Option 1: Quick Start (Easiest)
```bash
./start.sh
```
Then open `dashboard.html` in your browser.

### Option 2: Manual Start
```bash
# Install dependencies
pip install -r requirements.txt

# Start API server
python api_server.py

# Open dashboard.html in your browser
```

## 📁 Key Files

| File | Purpose |
|------|---------|
| `dashboard.html` | Main dashboard UI (open in browser) |
| `api_server.py` | Backend API (fetches data from DynamoDB) |
| `lambda_function_final.py` | AWS Lambda decoder (already deployed) |
| `start.sh` | One-command startup script |
| `README.md` | Complete documentation |

## 🎯 Next Steps

### 1. Test the Dashboard Now (on your desk)
```bash
python api_server.py
# Open dashboard.html
```

You should see:
- Current location on map
- Real-time telemetry (speed: 0, ignition: ON, etc.)
- Trip history (will populate when you toggle ignition)

### 2. Install in Your Vehicle

**Physical Installation:**
1. Mount device in vehicle (under dashboard recommended)
2. Connect to vehicle power:
   - Red → Battery positive (+12V)
   - Black → Ground
3. Optional: Connect ignition sense wire for automatic trip detection

**First Drive:**
1. Start your engine (dashboard should show "Ignition: ON")
2. Drive around
3. Turn off engine
4. Check dashboard - your first trip should appear!

### 3. Monitor Your Trips

The dashboard will automatically:
- Show your current location in real-time
- Track each drive as a separate trip
- Calculate distance, duration, max/avg speed
- Display your route on the map

## 📊 Dashboard Features

### Live View
- **Current location** - Blue marker on map
- **Speed** - Current speed in km/h
- **Ignition** - Green (ON) or Red (OFF)
- **GPS quality** - Number of satellites
- **Battery status** - Vehicle and device voltage

### Trip History
- **Trip list** - All recent trips (last 7 days)
- **Trip details** - Duration, distance, speeds
- **Route visualization** - See your path on the map
- **Click any trip** to view it on the map

### Auto-refresh
- Updates every 5 seconds automatically
- Toggle on/off with checkbox
- Manual refresh button available

## 🔍 Troubleshooting

### "Connection Error" in dashboard
→ Make sure `api_server.py` is running
→ Check http://localhost:5000/api/health

### No trips showing
→ Normal! Trips only appear when ignition cycles on → off
→ Once in vehicle, trips will appear automatically

### Map not loading
→ Check internet connection (map requires OpenStreetMap)
→ Try different browser

### No new data
→ Check device has power and GSM signal
→ Check AWS Lambda CloudWatch logs
→ Verify data in DynamoDB table

## 💡 Tips

**For Desktop Testing:**
- The device is currently sending data with ignition ON
- You won't see trip history yet (needs ignition cycles)
- You'll see current status and location

**For Vehicle Use:**
- Install near windshield for best GPS signal
- Connect to switched power to detect ignition automatically
- Keep dashboard open during drives to see real-time tracking

**Data Retention:**
- All data stored in DynamoDB
- Default: Keep last 7 days visible
- Older data still available (just filtered out)

## 🎨 Customization Ideas

1. **Change refresh rate** - Edit `dashboard.html` line ~47
2. **Add more stats** - Use IO elements from your device
3. **Export trips** - Add CSV download button
4. **Geofencing** - Alert when entering/leaving areas
5. **Multiple vehicles** - Add vehicle selector dropdown

## 📞 Support

**Check these if you have issues:**
1. AWS CloudWatch Logs (Lambda function)
2. DynamoDB table (`teltonika-events`)
3. Browser console (F12) for dashboard errors
4. API server terminal for backend errors

## ✨ What Makes This Cool

- **Real-time updates** - See your car move on the map
- **Automatic trips** - No manual tracking needed
- **Rich data** - Speed, voltage, GPS quality, and more
- **Historical playback** - Review past trips anytime
- **Professional dashboard** - Clean, modern UI

---

**You're all set! 🎉**

Start the API server and open the dashboard to begin tracking!
