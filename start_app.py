#!/usr/bin/env python3
"""
Quick Fix Script for FastAPI Backend
This script automatically fixes common issues and starts the backend
"""

import subprocess
import sys
import os
import time
import requests
from pathlib import Path

def install_missing_packages():
    """Install any missing packages"""
    required = ['fastapi', 'uvicorn', 'requests', 'pydantic', 'aiohttp']
    
    for package in required:
        try:
            __import__(package)
        except ImportError:
            print(f"📦 Installing {package}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
    
    print("✅ All packages installed!")

def create_simple_backend():
    """Create a simplified backend if main.py is missing or has issues"""
    backend_code = '''from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uuid
from datetime import datetime

app = FastAPI(title="Medical Consultation API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage
patients = {}
consultations = {}

# Data models
class PatientRegistration(BaseModel):
    name: str
    age: int
    gender: str
    phone: str
    medical_history: Optional[str] = ""
    current_medications: Optional[str] = ""
    allergies: Optional[str] = ""

class ConsultationRequest(BaseModel):
    patient_id: str
    specialization: str
    selected_symptoms: List[str]
    user_message: str
    use_ibm_api: Optional[bool] = False

# Specializations and symptoms
SPECIALIZATIONS = ["Dermatologist", "Gynecologist", "Cardiologist", "Neurologist", "Orthopedist"]

SYMPTOMS = {
    "Dermatologist": ["Skin rash", "Acne", "Dry skin", "Itching", "Skin discoloration"],
    "Gynecologist": ["Irregular periods", "Heavy bleeding", "Pelvic pain", "Vaginal discharge"],
    "Cardiologist": ["Chest pain", "Shortness of breath", "Heart palpitations", "Dizziness"],
    "Neurologist": ["Headaches", "Memory problems", "Seizures", "Numbness/tingling"],
    "Orthopedist": ["Joint pain", "Back pain", "Neck pain", "Muscle pain", "Stiffness"]
}

@app.get("/")
def root():
    return {"message": "Medical Consultation API is running", "status": "healthy"}

@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "huggingface_api": "demo_mode",
        "services": ["patient_registration", "consultation", "export"]
    }

@app.get("/api/specializations")
def get_specializations():
    return {"specializations": SPECIALIZATIONS}

@app.get("/api/symptoms/{specialization}")
def get_symptoms(specialization: str):
    return {"symptoms": SYMPTOMS.get(specialization, [])}

@app.post("/api/patients/register")
def register_patient(patient: PatientRegistration):
    patient_id = f"PAT_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(patients) + 1:03d}"
    
    patient_data = {
        "patient_id": patient_id,
        "name": patient.name,
        "age": patient.age,
        "gender": patient.gender,
        "phone": patient.phone,
        "medical_history": patient.medical_history,
        "current_medications": patient.current_medications,
        "allergies": patient.allergies,
        "registration_time": datetime.now().isoformat()
    }
    
    patients[patient_id] = patient_data
    consultations[patient_id] = []
    
    return {
        "success": True,
        "message": f"Patient registered successfully! Welcome, {patient.name}!",
        "patient_id": patient_id,
        "patient_data": patient_data
    }

@app.post("/api/consultation")
def create_consultation(request: ConsultationRequest):
    if request.patient_id not in patients:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    patient_data = patients[request.patient_id]
    symptoms_text = ", ".join(request.selected_symptoms) if request.selected_symptoms else "None"
    
    # Generate demo response
    doctor_response = f"""Thank you for your consultation, {patient_data['name']}.

Based on your concern about {request.user_message.lower()} and your selected symptoms ({symptoms_text}), here is my medical assessment:

**Assessment:**
- Your age ({patient_data['age']}) and symptoms suggest this needs proper medical evaluation
- The symptoms you've described are common in {request.specialization.lower()} practice

**Recommendations:**
1. **Lifestyle**: Maintain healthy habits and monitor your symptoms
2. **Monitoring**: Keep track of any changes in your condition
3. **Follow-up**: Consider scheduling an in-person consultation

**Important Medical Disclaimer:** This virtual consultation is for informational purposes only and does not replace professional medical advice, diagnosis, or treatment. Please schedule an in-person appointment for proper examination and diagnosis.

Do you have any other questions or concerns?"""
    
    consultation_record = {
        "timestamp": datetime.now().isoformat(),
        "specialization": request.specialization,
        "symptoms": request.selected_symptoms,
        "user_message": request.user_message,
        "doctor_response": doctor_response,
        "api_used": "Demo Mode"
    }
    
    consultations[request.patient_id].append(consultation_record)
    
    return {
        "response": doctor_response,
        "timestamp": consultation_record["timestamp"],
        "specialization": request.specialization,
        "symptoms": request.selected_symptoms,
        "api_used": "Demo Mode"
    }

@app.get("/api/export/{patient_id}")
def export_consultation_report(patient_id: str):
    if patient_id not in patients:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    patient_data = patients[patient_id]
    patient_consultations = consultations.get(patient_id, [])
    
    if not patient_consultations:
        raise HTTPException(status_code=404, detail="No consultation data found")
    
    report = f"""
MEDICAL CONSULTATION REPORT
Generated: {datetime.now().isoformat()}

PATIENT INFORMATION:
Name: {patient_data['name']}
Age: {patient_data['age']} years
Gender: {patient_data['gender']}
Phone: {patient_data['phone']}

CONSULTATION HISTORY:
"""
    
    for i, consultation in enumerate(patient_consultations, 1):
        symptoms_text = ", ".join(consultation['symptoms']) if consultation['symptoms'] else "None"
        report += f"""
CONSULTATION #{i} - {consultation['timestamp']}
Specialization: {consultation['specialization']}
Symptoms: {symptoms_text}
Patient Message: {consultation['user_message']}
Doctor Response: {consultation['doctor_response']}
{'='*80}
"""
    
    return {"patient_id": patient_id, "report": report, "generated_at": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
'''
    
    with open('backend_simple.py', 'w') as f:
        f.write(backend_code)
    
    print("✅ Created simplified backend (backend_simple.py)")

def start_backend():
    """Start the FastAPI backend"""
    print("🚀 Starting FastAPI backend...")
    
    # Try to start main.py first
    backend_file = 'main.py'
    if not Path(backend_file).exists():
        print("⚠️ main.py not found, creating simplified backend...")
        create_simple_backend()
        backend_file = 'backend_simple.py'
    
    try:
        # Start server
        process = subprocess.Popen([
            sys.executable, '-m', 'uvicorn', 
            f'{backend_file.replace(".py", "")}:app',
            '--host', '127.0.0.1',
            '--port', '7861',
            '--reload'
        ])
        
        # Wait for server to start
        print("⏳ Waiting for server to start...")
        for i in range(15):
            time.sleep(1)
            try:
                response = requests.get('http://localhost:8000/', timeout=2)
                if response.status_code == 200:
                    print("✅ FastAPI server is running!")
                    print("🌐 Backend URL: http://localhost:8000")
                    print("📚 API Docs: http://localhost:8000/docs")
                    return process
            except:
                print(f"   Waiting... ({i+1}/15)")
                continue
        
        print("❌ Server didn't start properly")
        process.terminate()
        return None
        
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return None

def main():
    print("🔧 FASTAPI BACKEND QUICK FIX")
    print("=" * 40)
    
    print("\n1️⃣ Installing/checking dependencies...")
    try:
        install_missing_packages()
    except Exception as e:
        print(f"❌ Error installing packages: {e}")
        return
    
    print("\n2️⃣ Starting FastAPI backend...")
    process = start_backend()
    
    if process:
        print("\n🎉 SUCCESS! Backend is running!")
        print("\n📝 Next steps:")
        print("   1. Keep this terminal window open")
        print("   2. Open a new terminal")
        print("   3. Run your frontend:")
        print("      python gradio_app.py")
        print("      # OR")
        print("      streamlit run streamlit_app.py")
        
        print("\n⏸️ Press Ctrl+C to stop the server...")
        
        try:
            # Keep server running until user stops it
            while True:
                time.sleep(1)
                if process.poll() is not None:
                    print("\n❌ Server stopped unexpectedly")
                    break
        except KeyboardInterrupt:
            print("\n🛑 Stopping server...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            print("✅ Server stopped successfully!")
    else:
        print("\n❌ Failed to start backend server")
        print("\n💡 Manual troubleshooting:")
        print("   1. Check if Python is properly installed")
        print("   2. Try: pip install fastapi uvicorn")
        print("   3. Try: python -m uvicorn main:app --host 127.0.0.1 --port 8000")

if __name__ == "__main__":
    main()