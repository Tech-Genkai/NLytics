#!/usr/bin/env python3
"""
NLytics Startup Script
Automated setup and launch for NLytics application
"""
import os
import sys
import subprocess
import platform
from pathlib import Path

def print_banner():
    """Print welcome banner"""
    print("\n" + "="*60)
    print("🚀 NLytics - Conversational Data Analytics")
    print("="*60 + "\n")

def check_python_version():
    """Check if Python version is 3.9 or higher"""
    print("📋 Checking Python version...")
    if sys.version_info < (3, 9):
        print("❌ Python 3.9 or higher is required")
        print(f"   Current version: {sys.version}")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

def install_dependencies():
    """Install required packages"""
    print("📥 Installing dependencies...")
    requirements_file = Path("backend") / "requirements.txt"
    
    if not requirements_file.exists():
        print(f"❌ Requirements file not found: {requirements_file}")
        sys.exit(1)
    
    try:
        # Use system Python's pip (works better than venv pip on Windows)
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(requirements_file)], check=True)
        print("✅ Dependencies installed")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        sys.exit(1)

def create_directories():
    """Ensure required directories exist"""
    print("📁 Creating required directories...")
    directories = [
        Path("data") / "uploads",
        Path("data") / "processed",
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    
    print("✅ Directories ready")

def cleanup_data_folders():
    """Clean up data/uploads and data/processed folders"""
    print("\n🧹 Cleaning up data folders...")
    
    cleanup_dirs = [
        Path("data") / "uploads",
        Path("data") / "processed",
        Path("backend") / "data" / "sessions"
    ]
    
    for dir_path in cleanup_dirs:
        if dir_path.exists():
            import shutil
            try:
                # Remove all files in directory except .gitkeep
                for item in dir_path.iterdir():
                    if item.name == ".gitkeep":
                        continue  # Skip .gitkeep files
                    
                    if item.is_file():
                        item.unlink()
                        print(f"   ✓ Deleted {item.name}")
                    elif item.is_dir():
                        shutil.rmtree(item)
                        print(f"   ✓ Deleted folder {item.name}")
            except Exception as e:
                print(f"   ⚠️ Could not clean {dir_path}: {e}")
    
    print("✅ Data folders cleaned")

def start_server():
    """Start the Flask server"""
    print("\n" + "="*60)
    print("🌟 Starting NLytics server...")
    print("="*60)
    print("\n📍 Server will be available at: http://localhost:5000")
    print("📍 Press Ctrl+C to stop the server\n")
    
    main_file = Path("backend") / "main.py"
    
    if not main_file.exists():
        print(f"❌ Main application file not found: {main_file}")
        sys.exit(1)
    
    try:
        # Run from backend directory using system Python
        backend_dir = Path("backend").absolute()
        subprocess.run([sys.executable, str(main_file.absolute())], cwd=str(backend_dir))
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped.")
        cleanup_data_folders()
        print("\nThanks for using NLytics!")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Server error: {e}")
        sys.exit(1)

def main():
    """Main startup sequence"""
    print_banner()
    
    # Check Python version
    check_python_version()
    
    # Install dependencies (skip venv, use system Python)
    install_dependencies()
    
    # Create required directories
    create_directories()
    
    # Start the server
    start_server()

if __name__ == "__main__":
    main()
