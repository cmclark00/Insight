#!/bin/bash

# Character Conversation Studio - Virtual Environment Runner

echo "📚 Character Conversation Studio"
echo "================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run ./install.sh first."
    exit 1
fi

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "⚠️  Ollama server doesn't appear to be running."
    echo "💡 Please start Ollama in another terminal: ollama serve"
    echo ""
    read -p "Press Enter to continue anyway, or Ctrl+C to exit..."
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Create data directories if they don't exist
mkdir -p data/{manuscripts,characters,vector_db}

echo "🚀 Starting Character Conversation Studio..."
echo "   Opening in your default browser at http://localhost:8501"
echo "   Press Ctrl+C to stop the application"
echo ""

# Run the Streamlit application
streamlit run app.py