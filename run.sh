#!/bin/bash

echo "=================================="
echo "Intelligent Coding Assistant"
echo "=================================="
echo ""

# Check if database exists
if [ ! -f "data/coding_assistant.db" ]; then
    echo "📦 Database not found. Initializing with sample data..."
    python load_sample_data.py
    echo ""
fi

echo "🚀 Starting FastAPI server..."
echo "📍 API: http://localhost:8000"
echo "📍 Docs: http://localhost:8000/docs"
echo "📍 Frontend: Open frontend/index.html in your browser"
echo ""
echo "Demo credentials:"
echo "  Email: demo@example.com"
echo "  Password: demo123"
echo ""

cd src
python main.py