#!/bin/bash
# VQMR Application Startup Script

set -e

# Switch to project root (script directory)
cd "$(dirname "$0")"

echo "Starting VQMR - Video Quality Metrics Report..."
echo "================================================"
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Error: Virtual environment not found!"
    echo "Please run: uv venv && uv pip install -r requirements.txt"
    exit 1
fi

mkdir -p jobs

export PYTHONPATH=.



echo "Starting Streamlit reports app..."
echo "   Reports: http://localhost:8079"
echo ""

# Start Streamlit in background
.venv/bin/streamlit run src/reports_app.py \
    --server.port 8079 \
    --server.address 0.0.0.0 \
    --server.headless true \
    --browser.gatherUsageStats false \
    > /dev/null 2>&1 &

STREAMLIT_PID=$!

# Cleanup function
cleanup() {
    echo ""
    echo "Shutting down applications..."
    kill $STREAMLIT_PID 2>/dev/null || true
}

trap cleanup EXIT
trap 'exit 0' SIGINT SIGTERM

echo "Starting FastAPI server..."
echo "   Web UI: http://localhost:8080"
echo "   API Docs: http://localhost:8080/api/docs"
echo ""

# Start FastAPI server (foreground)
.venv/bin/uvicorn src.main:app --reload --host 0.0.0.0 --port 8080

echo "Press Ctrl+C to stop servers"
echo ""
