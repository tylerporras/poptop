# 🚀 Real-Time Dashboard Deployment Guide

## 📦 What's New

Your enhanced dashboard now includes:

✅ **Trip Distance Tracking** - Real-time trip odometer with start/reset on ignition  
✅ **Connected to Railway API** - Live data from your production database  
✅ **Auto-Refresh (5 seconds)** - Perfect for monitoring during drives  
✅ **Mobile-Optimized** - Looks great on your phone  
✅ **Interactive Map** - Shows current location with auto-centering  
✅ **Trip Statistics** - Distance, duration, average speed  
✅ **Ignition Detection** - Automatically starts/stops trip tracking  

---

## 🔧 How to Deploy to GitHub Pages

### Option 1: Replace Existing Dashboard

1. **Clone your repo:**
   ```bash
   git clone https://github.com/tylerporras/poptop.git
   cd poptop
   ```

2. **Replace dashboard.html:**
   - Backup your current `dashboard.html`:
     ```bash
     mv dashboard.html dashboard_old.html
     ```
   - Copy the new `realtime_dashboard.html` as `dashboard.html`:
     ```bash
     cp realtime_dashboard.html dashboard.html
     ```

3. **Commit and push:**
   ```bash
   git add dashboard.html
   git commit -m "Enhanced dashboard with trip distance and live updates"
   git push origin main
   ```

4. **Access your dashboard:**
   - https://tylerporras.github.io/poptop/dashboard.html

---

### Option 2: Keep Both Dashboards

1. **Add as a separate file:**
   ```bash
   cd poptop
   cp realtime_dashboard.html dashboard_live.html
   git add dashboard_live.html
   git commit -m "Add enhanced live dashboard"
   git push origin main
   ```

2. **Access both versions:**
   - Original: https://tylerporras.github.io/poptop/dashboard.html
   - New Live: https://tylerporras.github.io/poptop/dashboard_live.html

---

## 📱 Using During Your Drive Tomorrow

### Before You Start:

1. **Open the dashboard on your phone:**
   - Go to: https://tylerporras.github.io/poptop/dashboard.html
   - Add to Home Screen (iPhone/Android) for easy access

2. **Check connection:**
   - You should see "LIVE" indicator pulsing green
   - VIN should show: WBAEP33485PF04957
   - Last update time should be recent

3. **Test ignition detection:**
   - Start your engine
   - Dashboard should show "Ignition: ON"
   - Trip distance should start at 0.0 km

### During Your Drive:

✅ **Dashboard Updates Every 5 Seconds**
- Speed updates in real-time
- Map follows your location automatically
- Trip distance increments as you drive
- Average speed calculates automatically

✅ **What You'll See:**
- **Current Speed** - Large, easy-to-read numbers
- **Trip Distance** - Meters converted to kilometers
- **Trip Duration** - Time since ignition on
- **Average Speed** - Based on distance and time
- **GPS Satellites** - Signal quality indicator
- **Map Position** - Auto-centers on your location

✅ **Battery Saving:**
- When you switch apps, refresh pauses
- Returns when you come back
- Prevents unnecessary battery drain

### After Your Drive:

- Turn off ignition
- Dashboard shows "Ignition: OFF"
- Trip stats freeze at final values
- Total odometer continues tracking

---

## 🎯 API Endpoints Being Used

The dashboard connects to your Railway API:

```
Base URL: https://poptop-production.up.railway.app/api

GET /latest/:imei - Gets real-time telemetry
```

**Data Retrieved:**
- GPS coordinates (latitude, longitude)
- Speed (km/h)
- Satellites count
- Trip odometer (meters) - IO element 199
- Total odometer (meters) - IO element 16
- Ignition status - IO element 239
- GSM signal strength
- External voltage
- All other IO elements

---

## 🔥 Key Features Explained

### 1. **Trip Distance Calculation**

The dashboard automatically tracks trip distance using the device's trip odometer:

- **Trip Start:** When ignition turns ON, saves current trip_odometer value
- **During Trip:** Calculates `current_trip_odometer - start_odometer`
- **Trip End:** When ignition turns OFF, resets for next trip
- **Display:** Converts meters to kilometers with 1 decimal place

**Example:**
```
Ignition ON  → Start: 5000m
Drive 10km   → Current: 15000m
Display: 10.0 km (15000 - 5000 = 10000m = 10km)
```

### 2. **Auto-Refresh System**

Updates every 5 seconds automatically:

```javascript
// Fetches latest data every 5000ms
setInterval(fetchLatestData, 5000)

// Pauses when browser tab hidden (saves battery)
document.addEventListener('visibilitychange', ...)
```

### 3. **Trip Statistics**

**Trip Duration:**
- Tracks time since ignition ON
- Displays as HH:MM format
- Example: `1:23` = 1 hour 23 minutes

**Average Speed:**
- Formula: `trip_distance / (duration_in_hours)`
- Only calculates when distance > 0.1 km
- Updates every 5 seconds

**Total Odometer:**
- Lifetime vehicle mileage
- From IO element 16
- Never resets

---

## 🛠️ Customization Options

### Change Refresh Rate

Edit line ~23:
```javascript
const REFRESH_INTERVAL = 5000; // Change to 3000 for 3 seconds, 10000 for 10 seconds
```

### Change Default IMEI

Edit line ~22:
```javascript
const DEFAULT_IMEI = '862464068525406'; // Your device IMEI
```

### Change API URL

Edit line ~21:
```javascript
const API_BASE_URL = 'https://poptop-production.up.railway.app/api';
```

---

## 📊 Tomorrow's Drive Preview

### Start of Drive:
```
╔═══════════════════════════════════╗
║  Ignition: ON ✅                 ║
║  Speed: 0 km/h                    ║
║  Trip Distance: 0.0 km            ║
║  Trip Duration: 0:00              ║
║  Avg Speed: 0 km/h                ║
║  Satellites: 13 (Excellent)       ║
║  GSM Signal: 1024                 ║
╚═══════════════════════════════════╝
```

### During Drive:
```
╔═══════════════════════════════════╗
║  Ignition: ON ✅                 ║
║  Speed: 65 km/h                   ║
║  Trip Distance: 42.3 km           ║
║  Trip Duration: 0:38              ║
║  Avg Speed: 66.8 km/h             ║
║  Satellites: 11 (Good)            ║
║  Total Odometer: 12,387.9 km      ║
╚═══════════════════════════════════╝
```

### End of Drive:
```
╔═══════════════════════════════════╗
║  Ignition: OFF ❌                ║
║  Speed: 0 km/h                    ║
║  Trip Distance: 87.6 km (SAVED)   ║
║  Trip Duration: 1:19 (SAVED)      ║
║  Avg Speed: 66.5 km/h             ║
║  Total Odometer: 12,433.2 km      ║
╚═══════════════════════════════════╝
```

---

## 🐛 Troubleshooting

### Dashboard Shows "Connection Error"

**Solution 1:** Check Railway API
```bash
curl https://poptop-production.up.railway.app/api/health
# Should return: {"status": "ok"}
```

**Solution 2:** Check device data
- Open AWS CloudWatch
- Check Lambda logs for errors
- Verify DynamoDB has recent records

**Solution 3:** CORS issue
- Check `api_server.py` has CORS enabled
- Should allow `https://tylerporras.github.io` origin

### Trip Distance Not Updating

**Check:**
1. Ignition is ON (dashboard shows green)
2. Device is sending trip_odometer (IO 199)
3. Vehicle is actually moving (GPS speed > 0)

### Map Not Showing Location

**Check:**
1. GPS has valid signal (satellites > 4)
2. Internet connection working
3. Browser has location permission (if needed)

---

## 🎉 Pre-Drive Checklist

**Tonight (Setup):**
- [ ] Deploy dashboard to GitHub Pages
- [ ] Test dashboard opens on phone
- [ ] Add to home screen
- [ ] Verify "LIVE" indicator is green
- [ ] Start engine and confirm ignition detection works
- [ ] Drive around the block to test trip tracking

**Tomorrow (Before Drive):**
- [ ] Open dashboard on phone
- [ ] Verify connection (green indicator)
- [ ] Start engine
- [ ] Confirm trip distance starts at 0.0 km
- [ ] Begin your journey! 🚗

**During Drive:**
- [ ] Dashboard updates automatically
- [ ] Trip distance increments
- [ ] Average speed calculates
- [ ] Map follows your position

---

## 💡 Pro Tips

1. **Add to Home Screen** - Makes it feel like a native app
2. **Keep Screen On** - Use your phone mount with power
3. **Check Satellites** - 7+ satellites = excellent tracking
4. **Watch Average Speed** - Fun to see efficiency!
5. **Screenshot Final Stats** - Save your trip records

---

## 🚀 What Makes This Dashboard Special

### Compared to Original Dashboard:

| Feature | Original | Enhanced |
|---------|----------|----------|
| Trip Distance | ❌ No | ✅ Yes (auto-tracked) |
| Auto-Refresh | Manual | ✅ Every 5 seconds |
| Mobile UI | Basic | ✅ Optimized |
| Trip Stats | No | ✅ Distance, duration, avg speed |
| Battery Saving | No | ✅ Pauses when hidden |
| Ignition Detection | Basic | ✅ Auto trip start/stop |

---

## 📞 Support

**If Something Goes Wrong:**

1. **API Issues:** Check Railway logs
2. **Device Issues:** Check CloudWatch logs
3. **Dashboard Issues:** Check browser console (F12)
4. **Data Issues:** Check DynamoDB table

---

**Have an amazing drive tomorrow! 🚗✨**

Your BMW will be fully tracked with real-time trip distance, live updates every 5 seconds, and all the stats you need!
