#!/bin/bash
# VQMR Application Startup Script

set -e

echo "Starting VQMR - Video Quality Metrics Report..."
echo "================================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found!"
    echo "Please run: python3 -m venv venv && ./venv/bin/pip install -r requirements.txt"
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found. Using default configuration."
    echo "To customize settings, copy .env.example to .env and edit it."
    echo ""
fi

# Create jobs directory if it doesn't exist
mkdir -p jobs

# Export PYTHONPATH to include current directory
export PYTHONPATH=.

echo "Starting server..."
echo "Access the application at: http://localhost:8080"
echo "API documentation at: http://localhost:8080/api/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
./venv/bin/uvicorn src.main:app --reload --host 0.0.0.0 --port 8080
