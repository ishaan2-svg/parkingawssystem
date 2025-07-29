#!/usr/bin/env python3
"""
SmartPark Pro Setup and Run Script
Automatically sets up virtual environment and runs the Flask backend
"""

import os
import sys
import subprocess
import json
import platform
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")

def check_virtual_environment():
    """Check if virtual environment exists and is valid"""
    venv_path = Path("venv")
    venv_python = get_venv_python()
    
    if not venv_path.exists():
        print("📦 No virtual environment found")
        return False
    
    if not venv_python.exists():
        print("⚠️  Virtual environment exists but Python executable not found")
        print("🔧 Virtual environment may be corrupted, will recreate...")
        return False
    
    # Test if the virtual environment works
    try:
        result = subprocess.run([str(venv_python), "--version"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ Found existing virtual environment")
            print(f"🐍 Using Python: {result.stdout.strip()}")
            return True
        else:
            print("⚠️  Virtual environment Python not working, will recreate...")
            return False
    except (subprocess.TimeoutExpired, subprocess.SubprocessError):
        print("⚠️  Virtual environment test failed, will recreate...")
        return False

def create_virtual_environment():
    """Create virtual environment if it doesn't exist or is invalid"""
    venv_path = Path("venv")
    
    # Check if existing venv is valid
    if check_virtual_environment():
        return True
    
    # Remove corrupted venv if it exists
    if venv_path.exists():
        print("🗑️  Removing corrupted virtual environment...")
        import shutil
        try:
            shutil.rmtree(venv_path)
            print("✅ Removed old virtual environment")
        except Exception as e:
            print(f"⚠️  Could not remove old venv: {e}")
            print("💡 Please manually delete the 'venv' folder and try again")
            return False
    
    print("🔧 Creating new virtual environment...")
    try:
        subprocess.check_call([sys.executable, "-m", "venv", "venv"])
        print("✅ Virtual environment created successfully")
        
        # Verify the new environment works
        if check_virtual_environment():
            return True
        else:
            print("❌ New virtual environment verification failed")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create virtual environment: {e}")
        print("💡 Make sure you have python3-venv installed:")
        print("   Ubuntu/Debian: sudo apt install python3-venv")
        print("   CentOS/RHEL: sudo yum install python3-venv")
        print("   Windows: Virtual environment should be available by default")
        return False

def get_venv_python():
    """Get the path to Python executable in virtual environment"""
    system = platform.system().lower()
    
    if system == "windows":
        return Path("venv/Scripts/python.exe")
    else:
        return Path("venv/bin/python")

def get_venv_pip():
    """Get the path to pip executable in virtual environment"""
    system = platform.system().lower()
    
    if system == "windows":
        return Path("venv/Scripts/pip.exe")
    else:
        return Path("venv/bin/pip")

def activate_venv_command():
    """Get the command to activate virtual environment"""
    system = platform.system().lower()
    
    if system == "windows":
        return "venv\\Scripts\\activate"
    else:
        return "source venv/bin/activate"

def check_packages_installed():
    """Check if required packages are installed in the virtual environment"""
    venv_python = get_venv_python()
    
    if not venv_python.exists():
        return False
    
    required_packages = ["flask", "flask_cors", "boto3", "pytz"]
    
    try:
        # Check if packages are installed
        result = subprocess.run([str(venv_python), "-c", 
                               "import flask, flask_cors, boto3, pytz; print('All packages installed')"], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ All required packages are already installed")
            return True
        else:
            print("📦 Some packages are missing, will install...")
            return False
            
    except (subprocess.TimeoutExpired, subprocess.SubprocessError):
        print("📦 Cannot verify packages, will install...")
        return False

def install_requirements():
    """Install required packages in virtual environment"""
    venv_pip = get_venv_pip()
    
    if not venv_pip.exists():
        print("❌ Virtual environment pip not found")
        return False
    
    # Check if packages are already installed
    if check_packages_installed():
        return True
    
    print("📦 Installing required packages in virtual environment...")
    try:
        # Upgrade pip first
        print("🔄 Upgrading pip...")
        subprocess.check_call([str(venv_pip), "install", "--upgrade", "pip"], 
                            stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        
        # Install requirements
        if Path("requirements.txt").exists():
            print("📄 Installing from requirements.txt...")
            subprocess.check_call([str(venv_pip), "install", "-r", "requirements.txt"],
                                stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        else:
            # Install packages manually if requirements.txt doesn't exist
            print("📦 Installing essential packages...")
            packages = ["Flask==2.3.3", "Flask-CORS==4.0.0", "boto3==1.28.62", "pytz==2024.1"]
            subprocess.check_call([str(venv_pip), "install"] + packages,
                                stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        
        print("✅ Packages installed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install packages: {e}")
        print("💡 Try activating venv manually and running:")
        print(f"   {activate_venv_command()}")
        print("   pip install Flask Flask-CORS boto3 pytz")
        return False

def setup_directories():
    """Create necessary directories"""
    directories = ['backups', 'logs']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"📁 Created directory: {directory}")

def check_files():
    """Check if required files exist"""
    required_files = ['app.py']
    missing_files = []
    
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing required files: {', '.join(missing_files)}")
        print("💡 Make sure app.py is in the same directory")
        return False
    
    print("✅ All required files found")
    return True

def create_requirements_file():
    """Create requirements.txt if it doesn't exist"""
    requirements_content = """Flask==2.3.3
Flask-CORS==4.0.0
boto3==1.28.62
botocore==1.31.62
pytz==2024.1
"""
    
    if not Path("requirements.txt").exists():
        with open("requirements.txt", "w") as f:
            f.write(requirements_content)
        print("📄 Created requirements.txt")
    
def create_config():
    """Create configuration file"""
    config = {
        "server": {
            "host": "0.0.0.0",
            "port": 8000,
            "debug": True
        },
        "parking": {
            "floors": 5,
            "divisions_per_floor": 10,
            "spots_per_division": 20
        },
        "aws": {
            "enabled": False,
            "region": "us-east-1",
            "bucket_name": "smartpark-data",
            "table_name": "smartpark-bookings"
        },
        "files": {
            "user_data": "user_data.json",
            "parking_layout": "parking_layout.json",
            "backup_dir": "backups"
        }
    }
    
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("⚙️  Created config.json")

def run_server():
    """Run the Flask server using virtual environment"""
    venv_python = get_venv_python()
    
    if not venv_python.exists():
        print("❌ Virtual environment Python not found")
        return False
    
    print("🌐 Starting SmartPark Pro Backend...")
    print(f"🔗 Server will be available at: http://localhost:8000")
    print("🔗 Open smartpark.html in your browser")
    print("💡 Use Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        subprocess.run([str(venv_python), "app.py"])
        return True
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
        return True
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        return False

def print_manual_instructions():
    """Print manual setup instructions"""
    activate_cmd = activate_venv_command()
    
    print("\n" + "=" * 60)
    print("📋 MANUAL SETUP INSTRUCTIONS")
    print("=" * 60)
    print("\n🔧 To run manually:")
    print(f"1. Activate virtual environment:")
    print(f"   {activate_cmd}")
    print("\n2. Install packages:")
    print("   pip install Flask Flask-CORS boto3")
    print("\n3. Run the server:")
    print("   python app.py")
    print("\n4. Open smartpark.html in your browser")
    print("   Demo login: KA-01-HH-1234 / demo123")

def main():
    """Main setup and run function"""
    print("🚀 SmartPark Pro Setup with Virtual Environment")
    print("=" * 60)
    
    # Check Python version
    check_python_version()
    
    # Check required files
    if not check_files():
        sys.exit(1)
    
    # Create requirements.txt if missing
    create_requirements_file()
    
    # Check/create virtual environment (reuses existing one)
    print("\n🔍 Checking virtual environment...")
    if not create_virtual_environment():
        print_manual_instructions()
        sys.exit(1)
    
    # Install/check requirements in venv (only if needed)
    print("\n📦 Checking packages...")
    if not install_requirements():
        print("⚠️  Package installation failed, but continuing...")
        print_manual_instructions()
    
    # Setup directories
    print("\n📁 Setting up directories...")
    setup_directories()
    
    # Create config
    print("\n⚙️  Creating configuration...")
    create_config()
    
    print("\n" + "=" * 60)
    print("✅ Setup completed successfully!")
    
    # Show status
    venv_status = "🟢 Ready" if check_virtual_environment() else "🔴 Not Ready"
    packages_status = "🟢 Installed" if check_packages_installed() else "🔴 Missing"
    
    print(f"\n📊 Environment Status:")
    print(f"   Virtual Environment: {venv_status}")
    print(f"   Required Packages: {packages_status}")
    
    print("\n📋 What's available:")
    print("📁 venv/ - Virtual environment (reused if existing)")
    print("📄 requirements.txt - Python dependencies")
    print("📄 config.json - Configuration file")
    print("📁 backups/ - Backup directory")
    print("📁 logs/ - Log directory")
    
    print("\n🎯 System Features:")
    print("✅ Virtual environment isolation")
    print("✅ Smart venv reuse (won't recreate existing)")
    print("✅ Package caching (skips if already installed)")
    print("✅ JSON file management")
    print("✅ REST API backend")
    print("✅ AWS integration ready")
    print("✅ 1000 parking spots simulation")
    
    print("\n🌐 API Endpoints (when server runs):")
    print("   http://localhost:8000/api/health")
    print("   http://localhost:8000/api/users")
    print("   http://localhost:8000/api/bookings")
    print("   http://localhost:8000/api/parking-layout")
    print("   http://localhost:8000/api/stats")
    
    # Ask if user wants to run the server now
    choice = input("\n🚀 Would you like to start the server now? (y/n): ").lower()
    
    if choice.startswith('y'):
        if not run_server():
            print_manual_instructions()
    else:
        print_manual_instructions()
        
    print("\n🎉 Happy parking! 🚗")
    print("💡 Next time you run this script, it will reuse your existing virtual environment")

if __name__ == "__main__":
    main()