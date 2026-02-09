#!/bin/bash

echo "=================================="
echo "Intelligent Coding Assistant"
echo "=================================="
echo ""

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"

# Check if database exists
if [ ! -f "data/coding_assistant.db" ]; then
    echo "📦 Database not found. Initializing with sample data..."
    python load_sample_data.py
    echo ""
fi

echo "🚀 Starting FastAPI server..."
echo "📍 API: http://localhost:${PORT}"
echo "📍 Docs: http://localhost:${PORT}/docs"
echo "📍 Frontend: Open frontend/index.html in your browser"
echo ""
echo "Demo credentials:"
echo "  Email: demo@example.com"
echo "  Password: demo123"
echo ""

HOST="${HOST}" PORT="${PORT}" python -m src.main
