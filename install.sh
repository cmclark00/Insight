#!/bin/bash

# Character Conversation Studio - Installation Script

echo "📚 Character Conversation Studio - Installation"
echo "==============================================="
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not found. Please install Python 3.8+."
    exit 1
fi

echo "✅ Python 3 found"

# Check if venv module is available
if ! python3 -c "import venv" &> /dev/null; then
    echo "⚠️  Python venv module not found. Installing python3-venv..."
    if command -v apt &> /dev/null; then
        sudo apt update && sudo apt install -y python3-venv python3-full
    else
        echo "❌ Please install python3-venv manually for your system."
        exit 1
    fi
fi

# Create virtual environment
echo "🔧 Creating virtual environment..."
python3 -m venv venv

if [ $? -ne 0 ]; then
    echo "❌ Failed to create virtual environment."
    exit 1
fi

echo "✅ Virtual environment created"

# Activate virtual environment and install dependencies
echo "📦 Installing dependencies..."
source venv/bin/activate

# Upgrade pip first
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies."
    exit 1
fi

echo "✅ Dependencies installed successfully!"

# Create data directories
echo "📁 Creating data directories..."
mkdir -p data/{manuscripts,characters,vector_db}
echo "✅ Data directories created"

echo ""
echo "🎉 Installation complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Install and start Ollama:"
echo "      curl -fsSL https://ollama.ai/install.sh | sh"
echo "      ollama serve"
echo ""
echo "   2. Download a model:"
echo "      ollama pull llama3.1:8b"
echo ""
echo "   3. Run the application:"
echo "      ./run_venv.sh"
echo ""
echo "   Or activate the environment manually:"
echo "      source venv/bin/activate"
echo "      streamlit run app.py"