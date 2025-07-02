#!/bin/bash

# Character Conversation Studio - Quick Start Script

echo "📚 Character Conversation Studio"
echo "================================="
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not found. Please install Python 3.8+."
    exit 1
fi

# Check if dependencies are installed
if ! python3 -c "import streamlit" &> /dev/null; then
    echo "📦 Installing dependencies..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies. Please run: pip3 install -r requirements.txt"
        exit 1
    fi
fi

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "⚠️  Ollama server doesn't appear to be running."
    echo "💡 Please start Ollama in another terminal: ollama serve"
    echo ""
    read -p "Press Enter to continue anyway, or Ctrl+C to exit..."
fi

# Create data directories if they don't exist
mkdir -p data/{manuscripts,characters,vector_db}

echo "🚀 Starting Character Conversation Studio..."
echo "   Opening in your default browser at http://localhost:8501"
echo "   Press Ctrl+C to stop the application"
echo ""

# Run the Streamlit application
streamlit run app.py