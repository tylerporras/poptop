# 🚗 Teltonika Vehicle Tracker

> Real-time GPS tracking dashboard for Teltonika FMM00A devices with trip analysis, interactive maps, and AWS integration

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![AWS](https://img.shields.io/badge/AWS-IoT%20%7C%20Lambda%20%7C%20DynamoDB-orange.svg)](https://aws.amazon.com/)

---

## ✨ Features

- 🗺️ **Real-time Location Tracking** - View your vehicle's current position on an interactive map
- 🚗 **Automatic Trip Detection** - Trips are detected based on ignition on/off cycles
- 📊 **Trip Analytics** - Distance, duration, max/avg speed, and route visualization
- ⚡ **Live Telemetry** - Monitor speed, GPS quality, battery voltage, and more
- 🔄 **Auto-refresh Dashboard** - Updates every 5 seconds automatically
- 📱 **Responsive Design** - Works on desktop, tablet, and mobile
- 🔒 **Your Data** - All data stored in your own AWS account
- 🎨 **Modern UI** - Clean, professional interface with Tailwind CSS

---

## 📸 Screenshots

### Dashboard Overview
<!-- Add your screenshot here -->
*Real-time vehicle location with telemetry data*

### Trip History
<!-- Add your screenshot here -->
*View and analyze all your trips*

### Trip Details
<!-- Add your screenshot here -->
*Detailed route visualization with statistics*

---

## 🏗️ Architecture

```
Teltonika FMM00A Device (GPS Tracker)
           ↓ TCP/Binary Data
Soracom Funnel (IoT Connectivity)
           ↓ MQTT/JSON
AWS IoT Core (Message Broker)
           ↓ Event Trigger
AWS Lambda (Binary Protocol Decoder)
           ↓ Parsed Data
DynamoDB (Data Storage)
           ↓ REST API
Flask Backend (Python)
           ↓ JSON
React Dashboard (Web Interface)
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- AWS account with configured credentials
- Teltonika FMM00A device with Soracom SIM
- DynamoDB table configured

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/teltonika-vehicle-tracker.git
   cd teltonika-vehicle-tracker
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. **Start the API server**
   ```bash
   python api_server.py
   ```

5. **Open the dashboard**
   - Open `dashboard.html` in your web browser
   - Or run: `python -m http.server 8000`
   - Visit: `http://localhost:8000/dashboard.html`

### One-Command Start

```bash
./start.sh
```

---

## 📖 Documentation

- [**Quick Start Guide**](QUICK_START.md) - Get up and running in minutes
- [**Complete Documentation**](README_DETAILED.md) - Full feature reference
- [**Architecture Details**](ARCHITECTURE.md) - System design and data flow
- [**GitHub Deployment**](GITHUB_DEPLOYMENT.md) - Deploy this project

---

## 🔧 Configuration

### API Server (`api_server.py`)

- **DynamoDB Table**: Set in `.env` or defaults to `teltonika-events`
- **AWS Region**: Defaults to `us-west-1`
- **Port**: Defaults to `5000`

### Dashboard (`dashboard.html`)

- **API URL**: Update line ~17 with your API server address
- **Default IMEI**: Update line ~18 with your device IMEI
- **Refresh Rate**: Modify line ~47 (default: 5 seconds)

### AWS Lambda

Deploy `lambda_function_final.py` to AWS Lambda with:
- Runtime: Python 3.8+
- Trigger: AWS IoT Rule
- Environment: 1024 MB memory, 30 second timeout

---

## 🎯 Use Cases

### Personal Use
- Track your daily commutes
- Monitor vehicle health
- Review driving patterns
- Family location sharing

### Business Use
- Fleet management
- Mileage tracking
- Route optimization
- Driver behavior analysis

---

## 🛠️ Tech Stack

**Backend:**
- Python 3.8+
- Flask (REST API)
- Boto3 (AWS SDK)
- AWS Lambda (Serverless decoder)
- DynamoDB (Data storage)

**Frontend:**
- React 18
- Leaflet.js (Interactive maps)
- Tailwind CSS (Styling)
- OpenStreetMap (Map tiles)

**Infrastructure:**
- AWS IoT Core (Message broker)
- Soracom (IoT connectivity)
- DynamoDB (NoSQL database)

**Hardware:**
- Teltonika FMM00A GPS tracker

---

## 📊 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/latest` | GET | Latest device data |
| `/api/history` | GET | Historical records |
| `/api/trips` | GET | Trip analysis |
| `/api/stats` | GET | Statistics summary |

See [API Documentation](README_DETAILED.md#api-endpoints) for details.

---

## 🎨 Customization

### Add More Telemetry

Edit `dashboard.html` to display additional IO elements:

```javascript
// Add custom IO elements
<div className="bg-gray-50 p-4 rounded-lg">
  <div className="text-gray-600 text-sm">Custom Sensor</div>
  <div className="text-xl font-bold text-gray-800">
    {currentData.io.my_sensor?.value || 0}
  </div>
</div>
```

### Change Map Style

Replace the map tile URL in `dashboard.html`:

```javascript
// Satellite view
L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}')

// Dark mode
L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png')
```

### Export Trip Data

Add a CSV export button to download trip data for analysis in Excel.

---

## 🔒 Security

**Current Implementation:**
- ⚠️ No authentication (development mode)
- ⚠️ Open CORS policy
- ⚠️ HTTP only

**Production Recommendations:**
- [ ] Add JWT authentication
- [ ] Enable HTTPS/TLS
- [ ] Restrict CORS to specific domains
- [ ] Use AWS API Gateway
- [ ] Enable DynamoDB encryption
- [ ] Implement rate limiting

See [Security Guidelines](README_DETAILED.md#security-considerations) for details.

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**Note:** This project integrates with third-party services:
- Teltonika is a trademark of UAB Teltonika Telematics
- AWS services are provided by Amazon Web Services
- Soracom is a trademark of Soracom, Inc.

This software is not affiliated with or endorsed by these companies.

---

## 🎓 Learn More

### Teltonika Protocol
- [Teltonika Wiki](https://wiki.teltonika-gps.com/)
- [Codec 8 Protocol](https://wiki.teltonika-gps.com/view/Codec#Codec_8)

### AWS IoT
- [AWS IoT Core Documentation](https://docs.aws.amazon.com/iot/)
- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [DynamoDB Documentation](https://docs.aws.amazon.com/dynamodb/)

### Frontend
- [Leaflet.js Documentation](https://leafletjs.com/)
- [React Documentation](https://react.dev/)
- [Tailwind CSS](https://tailwindcss.com/)

---

## 💬 Support

- 📖 [Read the Documentation](README_DETAILED.md)
- 🐛 [Report a Bug](https://github.com/YOUR_USERNAME/teltonika-vehicle-tracker/issues)
- 💡 [Request a Feature](https://github.com/YOUR_USERNAME/teltonika-vehicle-tracker/issues)
- 💬 [Discussions](https://github.com/YOUR_USERNAME/teltonika-vehicle-tracker/discussions)

---

## 🌟 Show Your Support

If you find this project useful, please consider:
- ⭐ Starring the repository
- 🐛 Reporting bugs
- 💡 Suggesting new features
- 🔀 Contributing code
- 📢 Sharing with others

---

## 📈 Roadmap

- [ ] Multi-vehicle support
- [ ] Geofencing with alerts
- [ ] Mobile app (React Native)
- [ ] Speed limit warnings
- [ ] Maintenance reminders
- [ ] Fuel efficiency tracking
- [ ] Driver behavior scoring
- [ ] Route playback with timeline
- [ ] Export trips to CSV/PDF
- [ ] Email/SMS notifications

---

## 🏆 Acknowledgments

- Teltonika for excellent GPS hardware
- AWS for reliable cloud infrastructure
- Soracom for IoT connectivity
- OpenStreetMap contributors
- Leaflet.js team
- Flask community

---

## 📊 Project Stats

![GitHub repo size](https://img.shields.io/github/repo-size/YOUR_USERNAME/teltonika-vehicle-tracker)
![GitHub stars](https://img.shields.io/github/stars/YOUR_USERNAME/teltonika-vehicle-tracker?style=social)
![GitHub forks](https://img.shields.io/github/forks/YOUR_USERNAME/teltonika-vehicle-tracker?style=social)
![GitHub issues](https://img.shields.io/github/issues/YOUR_USERNAME/teltonika-vehicle-tracker)

---

<div align="center">

**Made with ❤️ for vehicle tracking enthusiasts**

[Report Bug](https://github.com/YOUR_USERNAME/teltonika-vehicle-tracker/issues) · [Request Feature](https://github.com/YOUR_USERNAME/teltonika-vehicle-tracker/issues) · [Documentation](README_DETAILED.md)

</div>
