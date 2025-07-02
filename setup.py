#!/usr/bin/env python3
"""
Setup script for Character Conversation Studio
Helps users install dependencies and configure the application
"""

import subprocess
import sys
import os
import requests
import platform
from pathlib import Path

def print_banner():
    """Print application banner"""
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                Character Conversation Studio                 ║
    ║              Setup and Installation Script                   ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

def check_python_version():
    """Check if Python version is compatible"""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python {version.major}.{version.minor} detected. Python 3.8+ required.")
        return False
    else:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible!")
        return True

def install_python_dependencies():
    """Install Python dependencies from requirements.txt"""
    print("\n📦 Installing Python dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Python dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Python dependencies: {e}")
        return False

def check_ollama_installation():
    """Check if Ollama is installed"""
    print("\n🤖 Checking Ollama installation...")
    try:
        result = subprocess.run(["ollama", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Ollama found: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    
    print("❌ Ollama not found!")
    return False

def install_ollama():
    """Provide instructions for installing Ollama"""
    print("\n🚀 Installing Ollama...")
    system = platform.system().lower()
    
    if system in ["linux", "darwin"]:  # Linux or macOS
        print("📥 Downloading and installing Ollama...")
        try:
            # Download and run Ollama install script
            install_cmd = "curl -fsSL https://ollama.ai/install.sh | sh"
            subprocess.run(install_cmd, shell=True, check=True)
            print("✅ Ollama installed successfully!")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install Ollama automatically.")
            print("🔗 Please visit https://ollama.ai to install manually.")
            return False
    else:
        print("🔗 Windows detected. Please download Ollama from:")
        print("   https://ollama.ai/download/windows")
        print("   Install it and then run this setup script again.")
        return False

def check_ollama_server():
    """Check if Ollama server is running"""
    print("\n🔄 Checking Ollama server status...")
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama server is running!")
            return True
    except requests.exceptions.RequestException:
        pass
    
    print("⚠️  Ollama server is not running.")
    print("💡 Start it with: ollama serve")
    return False

def start_ollama_server():
    """Attempt to start Ollama server"""
    print("\n🚀 Starting Ollama server...")
    try:
        # Start Ollama server in background
        subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("✅ Ollama server started!")
        return True
    except Exception as e:
        print(f"❌ Failed to start Ollama server: {e}")
        print("💡 Try running 'ollama serve' manually in another terminal.")
        return False

def check_ollama_models():
    """Check available Ollama models"""
    print("\n📚 Checking available models...")
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        if result.returncode == 0:
            models = result.stdout.strip()
            if models and "NAME" in models:
                print("✅ Available models:")
                print(models)
                return True
    except Exception:
        pass
    
    print("⚠️  No models found.")
    return False

def download_recommended_model():
    """Download recommended model for character conversations"""
    print("\n⬇️  Downloading recommended model (llama3.1:8b)...")
    print("   This may take several minutes depending on your internet connection...")
    
    try:
        subprocess.run(["ollama", "pull", "llama3.1:8b"], check=True)
        print("✅ Model downloaded successfully!")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to download model.")
        print("💡 You can try a smaller model: ollama pull mistral:7b")
        return False

def create_data_directories():
    """Create necessary data directories"""
    print("\n📁 Creating data directories...")
    directories = ["data", "data/manuscripts", "data/characters", "data/vector_db"]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    
    print("✅ Data directories created!")

def run_application():
    """Launch the Streamlit application"""
    print("\n🚀 Launching Character Conversation Studio...")
    print("   The application will open in your web browser.")
    print("   Press Ctrl+C to stop the application when done.")
    
    try:
        subprocess.run(["streamlit", "run", "app.py"])
    except KeyboardInterrupt:
        print("\n👋 Application stopped. Goodbye!")
    except Exception as e:
        print(f"❌ Failed to start application: {e}")

def main():
    """Main setup routine"""
    print_banner()
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install Python dependencies
    if not install_python_dependencies():
        print("❌ Setup failed. Please check the error messages above.")
        sys.exit(1)
    
    # Check Ollama installation
    if not check_ollama_installation():
        if input("\n❓ Would you like to install Ollama? (y/N): ").lower().startswith('y'):
            if not install_ollama():
                print("❌ Please install Ollama manually and run setup again.")
                sys.exit(1)
        else:
            print("❌ Ollama is required. Please install it and run setup again.")
            sys.exit(1)
    
    # Check/start Ollama server
    if not check_ollama_server():
        if input("\n❓ Would you like to start the Ollama server? (y/N): ").lower().startswith('y'):
            start_ollama_server()
            # Give server time to start
            import time
            time.sleep(3)
    
    # Check for models
    if not check_ollama_models():
        if input("\n❓ Would you like to download the recommended model (llama3.1:8b)? (y/N): ").lower().startswith('y'):
            download_recommended_model()
    
    # Create directories
    create_data_directories()
    
    print("\n🎉 Setup complete!")
    print("\n📋 Next steps:")
    print("   1. Make sure Ollama server is running: ollama serve")
    print("   2. Launch the application: streamlit run app.py")
    print("   3. Open your browser to: http://localhost:8501")
    
    if input("\n❓ Would you like to launch the application now? (y/N): ").lower().startswith('y'):
        run_application()

if __name__ == "__main__":
    main()