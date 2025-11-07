#!/bin/bash

# Teltonika Tracker Dashboard - Quick Start Script

echo "🚗 Teltonika Vehicle Tracker Dashboard"
echo "======================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python 3 found"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip."
    exit 1
fi

echo "✅ pip3 found"

# Install dependencies
echo ""
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✅ Dependencies installed"

# Check AWS credentials
echo ""
echo "🔐 Checking AWS credentials..."
if ! aws sts get-caller-identity &> /dev/null; then
    echo "⚠️  AWS credentials not configured or invalid"
    echo "   Run: aws configure"
    echo "   Then run this script again"
    exit 1
fi

echo "✅ AWS credentials valid"

# Start the API server
echo ""
echo "🚀 Starting API server..."
echo "   Server will run at: http://localhost:5000"
echo ""
echo "📊 To view the dashboard:"
echo "   Open dashboard.html in your web browser"
echo "   Or run in another terminal: python3 -m http.server 8000"
echo "   Then visit: http://localhost:8000/dashboard.html"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""
echo "========================================"
echo ""

# Start the Flask API server
python3 api_server.py
