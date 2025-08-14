#!/usr/bin/env python3
"""
Medical Consultation System - Startup Script
This script provides an easy way to start the entire system
"""

import subprocess
import sys
import os
import time
import threading
import webbrowser
from pathlib import Path

def print_banner():
    banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                     🏥 MEDICAL CONSULTATION SYSTEM 🏥                        ║
║                                                                              ║
║  FastAPI Backend + Gradio/Streamlit Frontend                                ║
║  Integrated with HuggingFace & IBM Watson APIs                              ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_dependencies():
    """Check if all required packages are installed"""
    required_packages = [
        'fastapi', 'uvicorn', 'gradio', 'streamlit', 
        'requests', 'aiohttp', 'pydantic'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("📦 Installing missing packages...")
        
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install'
            ] + missing_packages)
            print("✅ All packages installed successfully!")
        except subprocess.CalledProcessError:
            print("❌ Failed to install packages. Please install manually:")
            print(f"pip install {' '.join(missing_packages)}")
            return False
    else:
        print("✅ All required packages are installed!")
    
    return True

def check_files():
    """Check if all required files exist"""
    required_files = ['main.py', 'gradio_app.py']
    missing_files = []
    
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing files: {', '.join(missing_files)}")
        print("Please ensure all project files are in the current directory.")
        return False
    else:
        print("✅ All project files found!")
    
    return True

def start_fastapi_server():
    """Start the FastAPI backend server"""
    print("🚀 Starting FastAPI backend server...")
    try:
        # Start FastAPI server
        process = subprocess.Popen([
            sys.executable, '-m', 'uvicorn', 'main:app',
            '--host', '0.0.0.0',
            '--port', '8000',
            '--reload'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a moment for server to start
        time.sleep(3)
        
        # Check if server is running
        if process.poll() is None:
            print("✅ FastAPI server started successfully on http://localhost:8000")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Failed to start FastAPI server")
            print(f"Error: {stderr.decode()}")
            return None
            
    except Exception as e:
        print(f"❌ Error starting FastAPI server: {e}")
        return None

def start_gradio_frontend():
    """Start the Gradio frontend"""
    print("🎨 Starting Gradio frontend...")
    try:
        process = subprocess.Popen([
            sys.executable, 'gradio_app.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        time.sleep(2)
        
        if process.poll() is None:
            print("✅ Gradio frontend started successfully on http://localhost:8000")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Failed to start Gradio frontend")
            print(f"Error: {stderr.decode()}")
            return None
            
    except Exception as e:
        print(f"❌ Error starting Gradio frontend: {e}")
        return None

def start_streamlit_frontend():
    """Start the Streamlit frontend"""
    print("🎨 Starting Streamlit frontend...")
    try:
        process = subprocess.Popen([
            sys.executable, '-m', 'streamlit', 'run', 'streamlit_app.py',
            '--server.port', '8501',
            '--server.headless', 'true'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        time.sleep(3)
        
        if process.poll() is None:
            print("✅ Streamlit frontend started successfully on http://localhost:8000")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Failed to start Streamlit frontend")
            print(f"Error: {stderr.decode()}")
            return None
            
    except Exception as e:
        print(f"❌ Error starting Streamlit frontend: {e}")
        return None

def open_browser(urls, delay=5):
    """Open browser tabs after a delay"""
    def delayed_open():
        time.sleep(delay)
        for url in urls:
            try:
                webbrowser.open(url)
                time.sleep(1)
            except Exception as e:
                print(f"Could not open {url}: {e}")
    
    threading.Thread(target=delayed_open, daemon=True).start()

def main():
    print_banner()
    
    # Check dependencies and files
    if not check_dependencies():
        return
    
    if not check_files():
        return
    
    print("\n📋 Choose startup option:")
    print("1. Full system (FastAPI + Gradio)")
    print("2. Full system (FastAPI + Streamlit)")
    print("3. Full system (FastAPI + Both frontends)")
    print("4. Backend only (FastAPI)")
    print("5. Exit")
    
    try:
        choice = input("\nEnter your choice (1-5): ").strip()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        return
    
    processes = []
    urls_to_open = []
    
    if choice in ['1', '2', '3', '4']:
        # Start FastAPI backend
        fastapi_process = start_fastapi_server()
        if not fastapi_process:
            print("❌ Cannot continue without backend server")
            return
        processes.append(fastapi_process)
        urls_to_open.append('http://localhost:8000/docs')
    
    if choice == '1' or choice == '3':
        # Start Gradio frontend
        gradio_process = start_gradio_frontend()
        if gradio_process:
            processes.append(gradio_process)
            urls_to_open.append('http://localhost:8000')
    
    if choice == '2' or choice == '3':
        # Start Streamlit frontend
        streamlit_process = start_streamlit_frontend()
        if streamlit_process:
            processes.append(streamlit_process)
            urls_to_open.append('http://localhost:8000')
    
    if choice == '5':
        print("👋 Goodbye!")
        return
    
    if choice not in ['1', '2', '3', '4', '5']:
        print("❌ Invalid choice. Please run the script again.")
        return
    
    if not processes:
        print("❌ No services started successfully")
        return
    
    # Open browser tabs
    if urls_to_open:
        print(f"🌐 Opening browser tabs in 5 seconds...")
        open_browser(urls_to_open)
    
    # Show running services
    print(f"\n🎉 System started successfully!")
    print("📊 Running services:")
    if any('main:app' in str(p.args) for p in processes):
        print("   • FastAPI Backend: http://localhost:8000")
        print("   • API Documentation: http://localhost:8000/docs")
    if any('gradio_app.py' in str(p.args) for p in processes):
        print("   • Gradio Frontend: http://localhost:8000")
    if any('streamlit_app.py' in str(p.args) for p in processes):
        print("   • Streamlit Frontend: http://localhost:8000")
    
    print(f"\n⚙️  Configuration tips:")
    print("   • Add your HuggingFace API token for AI responses")
    print("   • Add your IBM Watson credentials for enhanced AI")
    print("   • System works in demo mode without API keys")
    
    print(f"\n🔧 To stop all services, press Ctrl+C")
    
    try:
        # Wait for user interrupt
        while True:
            time.sleep(1)
            # Check if any process has terminated
            for process in processes[:]:
                if process.poll() is not None:
                    processes.remove(process)
                    print(f"⚠️  A service has stopped unexpectedly")
            
            if not processes:
                print("❌ All services have stopped")
                break
                
    except KeyboardInterrupt:
        print(f"\n🛑 Stopping all services...")
        
        for process in processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            except Exception as e:
                print(f"Error stopping process: {e}")
        
        print("✅ All services stopped successfully!")
        print("👋 Thank you for using the Medical Consultation System!")

if __name__ == "__main__":
    main()
    