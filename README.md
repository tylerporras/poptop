# POPTOP Fleet Tracker - Enhanced Edition

**Connected to Teltonika Pipeline | All 53 IO Elements Displayed**

---

## 🚀 Quick Start

```powershell
.\start_poptop.ps1
```

That's it! The script will:
- Install dependencies if needed
- Start the API server
- Open the dashboard in your browser

---

## 📁 Files Overview

| File | Purpose |
|------|---------|
| `api_server_NEW.py` | API server (Timescale Cloud connection) |
| `dashboard_ENHANCED.html` | Dashboard (53 IO elements) |
| `start_poptop.ps1` | Automated startup script |
| `INTEGRATION_COMPLETE.md` | Full integration guide |
| `POPTOP_INTEGRATION_SUMMARY.md` | Technical summary |
| `README.md` | This file |

---

## 📊 What's Displayed

### Dashboard Shows ALL 53 IO Elements:

**⚡ Power & Battery** (4)
- External voltage, internal voltage, current, battery level

**🚗 Vehicle Status** (4)
- Ignition, movement, total odometer, trip odometer

**🔧 OBD-II Data** (25+)
- VIN, fuel level, coolant temp, engine load, throttle, DTC codes, and more

**📱 Cellular Network** (5)
- GSM signal, ICCID, IMSI, cell tower ID, operator code

**🛰️ GPS/GNSS** (5)
- GNSS status, PDOP, HDOP, NMEA coordinates

**📋 Other Elements** (10+)
- Digital inputs, analog inputs, sleep mode, data mode, etc.

---

## 🚗 Your Fleet

The dashboard tracks **3 devices**:

1. **862464068525406** - 2008 Mercedes Sprinter (VIN: WD0PF445585238717)
2. **862464068511489** - 2008 Toyota (VIN: 5TELU42N88Z495934)
3. **862464068525638** - 2015 Lexus NX (VIN: 2T2BK1BA5FC336915)

Switch between devices using the dropdown selector.

---

## 🔧 Manual Operation

### Start API Server
```powershell
python api_server_NEW.py
```

### Open Dashboard
Just double-click `dashboard_ENHANCED.html` or drag it into your browser.

---

## ✅ Features

- ✅ Real-time location tracking on interactive map
- ✅ All 53 IO elements organized in categories
- ✅ Trip history with full telemetry
- ✅ Multi-device fleet support
- ✅ Auto-refresh every 5 seconds
- ✅ Color-coded ignition status (green = ON, red = OFF)
- ✅ Statistics (distance, max speed, record count)
- ✅ VIN identification
- ✅ DTC/Check Engine Light monitoring

---

## 🔍 Troubleshooting

**"ModuleNotFoundError: No module named 'psycopg2'"**
```powershell
pip install psycopg2-binary flask flask-cors
```

**Dashboard shows "Connection Error"**
- Make sure API server is running (`python api_server_NEW.py`)
- Check that it's on port 5000
- Look for errors in the Python terminal window

**No data showing**
- Verify devices are actively transmitting (check Gran Autismo or S3)
- Confirm selected IMEI is correct
- Check browser console (F12) for errors

---

## 📚 Documentation

For complete details, see:
- `INTEGRATION_COMPLETE.md` - Full integration guide
- `POPTOP_INTEGRATION_SUMMARY.md` - Technical summary

---

## 🎊 Success!

You now have a fully functional fleet tracking dashboard with **complete telemetry visibility**. All 53 IO elements from your Teltonika devices are captured and beautifully displayed!

**Data Pipeline:**
```
Teltonika Devices → AWS IoT Core → Lambda → Timescale Cloud → POPTOP Dashboard
```

**Enjoy your enhanced fleet tracker!** 🚗📊✨

---

**Last Updated:** November 14, 2025  
**Status:** ✅ Ready to Use
