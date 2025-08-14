#!/usr/bin/env python3
"""
Medical Consultation System - Connection Troubleshooting Tool
This script helps diagnose and fix connection issues
"""

import subprocess
import sys
import requests
import time
import socket
import psutil
import os
from pathlib import Path

def print_header():
    print("=" * 70)
    print("🔧 MEDICAL CONSULTATION SYSTEM - TROUBLESHOOTING TOOL")
    print("=" * 70)

def check_python_version():
    """Check Python version compatibility"""
    print("\n1️⃣ Checking Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Requires Python 3.8+")
        return False

def check_required_files():
    """Check if all required files exist"""
    print("\n2️⃣ Checking required files...")
    required_files = ['main.py', 'gradio_app.py', 'streamlit_app.py']
    all_exist = True
    
    for file in required_files:
        if Path(file).exists():
            print(f"✅ {file} - Found")
        else:
            print(f"❌ {file} - Missing")
            all_exist = False
    
    return all_exist

def check_dependencies():
    """Check and install missing dependencies"""
    print("\n3️⃣ Checking dependencies...")
    required_packages = {
        'fastapi': 'FastAPI web framework',
        'uvicorn': 'ASGI server',
        'requests': 'HTTP library',
        'gradio': 'Gradio frontend',
        'streamlit': 'Streamlit frontend',
        'pydantic': 'Data validation',
        'aiohttp': 'Async HTTP client'
    }
    
    missing_packages = []
    
    for package, description in required_packages.items():
        try:
            __import__(package)
            print(f"✅ {package} - Installed ({description})")
        except ImportError:
            print(f"❌ {package} - Missing ({description})")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n📦 Installing missing packages: {', '.join(missing_packages)}")
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install'
            ] + missing_packages, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("✅ All packages installed successfully!")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install packages: {e}")
            print("💡 Try installing manually:")
            print(f"   pip install {' '.join(missing_packages)}")
            return False
    
    return True

def check_port_availability(port):
    """Check if a port is available"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('localhost', port))
            return True
        except socket.error:
            return False

def find_process_on_port(port):
    """Find what process is using a port"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            for conn in proc.connections():
                if conn.laddr.port == port:
                    return proc.info
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None

def check_ports():
    """Check port availability"""
    print("\n4️⃣ Checking port availability...")
    
    ports_to_check = {
        8000: "FastAPI Backend",
        7860: "Gradio Frontend", 
        8501: "Streamlit Frontend"
    }
    
    all_available = True
    
    for port, service in ports_to_check.items():
        if check_port_availability(port):
            print(f"✅ Port {port} - Available ({service})")
        else:
            print(f"❌ Port {port} - In use ({service})")
            process = find_process_on_port(port)
            if process:
                print(f"   🔍 Used by: {process['name']} (PID: {process['pid']})")
            all_available = False
    
    return all_available

def test_fastapi_connection():
    """Test FastAPI server connection"""
    print("\n5️⃣ Testing FastAPI server connection...")
    
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            print("✅ FastAPI server is running and accessible")
            return True
        else:
            print(f"❌ FastAPI server responded with status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to FastAPI server - Server not running")
        return False
    except requests.exceptions.Timeout:
        print("❌ Connection timeout - Server might be overloaded")
        return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def start_fastapi_server():
    """Start the FastAPI server"""
    print("\n6️⃣ Starting FastAPI server...")
    
    if not Path('main.py').exists():
        print("❌ main.py not found. Cannot start server.")
        return False
    
    try:
        # Try to start the server
        print("🚀 Launching FastAPI server...")
        
        # Check if uvicorn is available
        try:
            import uvicorn
            print("✅ Using uvicorn server")
            
            # Start server in a way that doesn't block this script
            process = subprocess.Popen([
                sys.executable, '-m', 'uvicorn', 'main:app',
                '--host', '127.0.0.1',
                '--port', '7861',
                '--reload'
            ])
            
            # Wait for server to start
            print("⏳ Waiting for server to start...")
            for i in range(10):
                time.sleep(1)
                if test_fastapi_connection():
                    print("✅ FastAPI server started successfully!")
                    return True
                print(f"   Waiting... ({i+1}/10)")
            
            print("❌ Server didn't start within 10 seconds")
            process.terminate()
            return False
            
        except ImportError:
            print("❌ uvicorn not found. Installing...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'uvicorn[standard]'])
            return start_fastapi_server()  # Retry after installation
            
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        return False

def run_diagnostic():
    """Run full diagnostic"""
    print_header()
    
    all_checks_passed = True
    
    # Run all checks
    checks = [
        ("Python Version", check_python_version),
        ("Required Files", check_required_files), 
        ("Dependencies", check_dependencies),
        ("Port Availability", check_ports),
    ]
    
    for check_name, check_func in checks:
        if not check_func():
            all_checks_passed = False
    
    # Test server connection
    server_running = test_fastapi_connection()
    
    print("\n" + "=" * 70)
    print("📊 DIAGNOSTIC SUMMARY")
    print("=" * 70)
    
    if all_checks_passed and server_running:
        print("🎉 All checks passed! System is ready.")
        return True
    elif all_checks_passed and not server_running:
        print("⚠️  System setup is correct, but FastAPI server is not running.")
        
        answer = input("\n❓ Would you like me to start the FastAPI server? (y/n): ").lower()
        if answer in ['y', 'yes']:
            return start_fastapi_server()
        else:
            print("\n💡 To start the server manually, run:")
            print("   python main.py")
            print("   # OR")
            print("   uvicorn main:app --host 127.0.0.1 --port 8000 --reload")
            return False
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        return False

def main():
    """Main function"""
    success = run_diagnostic()
    
    if success:
        print("\n🌟 SUCCESS! Your Medical Consultation System is ready!")
        print("\n🔗 Access URLs:")
        print("   • FastAPI Backend: http://localhost:8000")
        print("   • API Documentation: http://localhost:8000/docs") 
        print("   • Gradio Frontend: http://localhost:7860")
        print("   • Streamlit Frontend: http://localhost:8501")
        
        print("\n📝 Next steps:")
        print("   1. Keep this terminal open (FastAPI server is running)")
        print("   2. Open a new terminal")
        print("   3. Run: python gradio_app.py  OR  streamlit run streamlit_app.py")
        
        try:
            input("\n⏸️  Press Enter to stop the FastAPI server...")
        except KeyboardInterrupt:
            pass
        finally:
            print("\n👋 FastAPI server stopped. Goodbye!")
    else:
        print("\n💡 TROUBLESHOOTING TIPS:")
        print("   • Make sure all files are in the same directory")
        print("   • Check if antivirus is blocking Python")
        print("   • Try running as administrator/sudo if needed")
        print("   • Ensure no other services are using port 8000")
        
        print("\n🆘 If problems persist:")
        print("   1. Restart your computer")
        print("   2. Reinstall Python packages: pip install --force-reinstall fastapi uvicorn")
        print("   3. Check firewall settings")

if __name__ == "__main__":
    main()