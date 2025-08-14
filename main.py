# main.py - FastAPI Backend
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
import requests
import json
import os
from enum import Enum

# Initialize FastAPI app
app = FastAPI(title="Medical Consultation API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Configuration
HUGGINGFACE_API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN", "your_huggingface_token_here")
IBM_API_KEY = os.getenv("IBM_API_KEY", "your_ibm_api_key_here")
IBM_URL = os.getenv("IBM_URL", "your_ibm_watson_url_here")

# Doctor specializations
class Specialization(str, Enum):
    DERMATOLOGIST = "Dermatologist"
    GYNECOLOGIST = "Gynecologist"
    CARDIOLOGIST = "Cardiologist"
    NEUROLOGIST = "Neurologist"
    ORTHOPEDIST = "Orthopedist"

# Symptoms mapping
SYMPTOMS = {
    Specialization.DERMATOLOGIST: [
        "Skin rash", "Acne", "Dry skin", "Itching", "Skin discoloration",
        "Hair loss", "Nail problems", "Moles/skin growths", "Eczema", "Psoriasis"
    ],
    Specialization.GYNECOLOGIST: [
        "Irregular periods", "Heavy bleeding", "Pelvic pain", "Vaginal discharge",
        "Painful periods", "Missed periods", "Breast pain", "Urinary issues",
        "Menopause symptoms", "Fertility concerns"
    ],
    Specialization.CARDIOLOGIST: [
        "Chest pain", "Shortness of breath", "Heart palpitations", "Dizziness",
        "Fatigue", "Swollen legs/ankles", "High blood pressure", "Irregular heartbeat",
        "Fainting", "Exercise intolerance"
    ],
    Specialization.NEUROLOGIST: [
        "Headaches", "Memory problems", "Seizures", "Numbness/tingling",
        "Muscle weakness", "Balance problems", "Vision changes", "Speech difficulties",
        "Tremors", "Sleep disorders"
    ],
    Specialization.ORTHOPEDIST: [
        "Joint pain", "Back pain", "Neck pain", "Muscle pain", "Stiffness",
        "Limited range of motion", "Swelling", "Bone pain", "Sports injury", "Arthritis"
    ]
}

# Pydantic Models
class PatientRegistration(BaseModel):
    name: str
    age: int
    gender: str
    phone: str
    medical_history: Optional[str] = ""
    current_medications: Optional[str] = ""
    allergies: Optional[str] = ""
    
    @validator('age')
    def validate_age(cls, v):
        if v <= 0 or v > 150:
            raise ValueError('Age must be between 1 and 150')
        return v
    
    @validator('name', 'phone')
    def validate_required_fields(cls, v):
        if not v or not v.strip():
            raise ValueError('This field is required')
        return v.strip()

class ConsultationRequest(BaseModel):
    specialization: Specialization
    selected_symptoms: List[str]
    message: str
    patient_id: str

class ConsultationResponse(BaseModel):
    doctor_response: str
    timestamp: str
    consultation_id: str

class ChatMessage(BaseModel):
    patient_message: str
    doctor_response: str
    timestamp: str
    symptoms: List[str]

# In-memory storage (replace with database in production)
patients_db: Dict[str, Dict[str, Any]] = {}
consultations_db: Dict[str, List[ChatMessage]] = {}

# Hugging Face API Integration
class HuggingFaceClient:
    def __init__(self, api_token: str):
        self.api_token = api_token
        self.headers = {"Authorization": f"Bearer {api_token}"}
        self.api_url = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-large"
    
    def generate_response(self, prompt: str) -> str:
        try:
            payload = {"inputs": prompt, "parameters": {"max_length": 500, "temperature": 0.7}}
            response = requests.post(self.api_url, headers=self.headers, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get("generated_text", "").replace(prompt, "").strip()
            return None
        except Exception as e:
            print(f"Hugging Face API error: {e}")
            return None

# IBM Watson Integration
class IBMWatsonClient:
    def __init__(self, api_key: str, url: str):
        self.api_key = api_key
        self.url = url
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
    
    def generate_response(self, prompt: str) -> str:
        try:
            payload = {
                "input": prompt,
                "parameters": {
                    "max_new_tokens": 500,
                    "temperature": 0.7
                }
            }
            response = requests.post(f"{self.url}/ml/v1/text/generation", 
                                   headers=self.headers, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                return result.get("results", [{}])[0].get("generated_text", "")
            return None
        except Exception as e:
            print(f"IBM Watson API error: {e}")
            return None

# Initialize AI clients
hf_client = HuggingFaceClient(HUGGINGFACE_API_TOKEN)
ibm_client = IBMWatsonClient(IBM_API_KEY, IBM_URL)

# Helper Functions
def generate_patient_id(name: str, phone: str) -> str:
    """Generate unique patient ID"""
    return f"pat_{hash(name + phone + str(datetime.now().timestamp()))}"

def create_medical_prompt(patient_info: Dict, specialization: str, symptoms: List[str], message: str) -> str:
    """Create medical consultation prompt"""
    patient_details = f"""
    Patient Information:
    - Name: {patient_info['name']}
    - Age: {patient_info['age']}
    - Gender: {patient_info['gender']}
    - Medical History: {patient_info.get('medical_history', 'None provided')}
    - Current Medications: {patient_info.get('current_medications', 'None')}
    - Allergies: {patient_info.get('allergies', 'None')}
    """
    
    symptoms_text = ", ".join(symptoms) if symptoms else "None selected"
    
    return f"""
    You are an experienced {specialization} providing medical consultation.
    
    {patient_details}
    
    Selected Symptoms: {symptoms_text}
    
    Guidelines:
    1. Be professional, empathetic, and thorough
    2. Ask relevant follow-up questions if needed
    3. Provide medical advice based on symptoms and patient history
    4. Suggest appropriate medications when necessary (include dosage and duration)
    5. Recommend when to seek immediate medical attention
    6. Always remind that this is a consultation and not a replacement for in-person examination
    7. Be specific about medication names, dosages, and instructions
    
    Patient's message: {message}
    
    Doctor's response:"""

def get_fallback_response(specialization: str, symptoms: List[str], message: str, patient_name: str, patient_age: int) -> str:
    """Generate fallback response when APIs are not available"""
    symptoms_text = ", ".join(symptoms) if symptoms else "no specific symptoms selected"
    
    fallback_responses = {
        "Dermatologist": f"""
        Thank you for your consultation, {patient_name}. 

        Based on your concern about {message.lower()} and the symptoms you've selected ({symptoms_text}), I can provide the following guidance:

        **Assessment:**
        - Your age ({patient_age}) and symptoms suggest this could be a common dermatological condition
        - The combination of {symptoms_text} needs proper evaluation

        **Recommendations:**
        1. **Topical Treatment**: Consider applying a gentle moisturizer twice daily
        2. **Avoid Irritants**: Stay away from harsh soaps and fragrances
        3. **Medication**: You may try over-the-counter hydrocortisone cream (0.5%) for 5-7 days

        **When to seek immediate care:**
        - If symptoms worsen rapidly
        - Signs of infection (pus, increased redness, warmth)
        - If you develop fever

        **Important:** This is a virtual consultation. Please visit a dermatologist in person for proper examination and diagnosis.

        Do you have any other concerns or questions?
        """,
        
        "Cardiologist": f"""
        Hello {patient_name}, 

        Thank you for consulting me about {message.lower()}. Given your symptoms ({symptoms_text}), let me provide you with some guidance:

        **Assessment:**
        - At {patient_age} years old, cardiovascular health is important to monitor
        - Your symptoms need careful evaluation

        **Immediate Recommendations:**
        1. **Lifestyle**: Maintain regular exercise (as tolerated)
        2. **Diet**: Reduce sodium intake, increase fruits and vegetables
        3. **Monitoring**: Check blood pressure regularly

        **Medication (if appropriate):**
        - Consider low-dose aspirin (81mg daily) - consult your physician first
        - If you have hypertension: ACE inhibitors may be recommended

        **⚠️ Seek immediate medical attention if:**
        - Severe chest pain
        - Shortness of breath at rest
        - Fainting or severe dizziness

        **Important:** Cardiac conditions require in-person evaluation. Please schedule an appointment for proper testing (ECG, echocardiogram if needed).

        Any other questions about your heart health?
        """,
        
        "Gynecologist": f"""
        Dear {patient_name},

        Thank you for your consultation regarding {message.lower()}. Considering your symptoms ({symptoms_text}), here's my assessment:

        **Clinical Evaluation:**
        - Your age ({patient_age}) and symptoms provide important context
        - These concerns are common and often treatable

        **Treatment Recommendations:**
        1. **Lifestyle**: Maintain good hygiene, wear breathable cotton underwear
        2. **Diet**: Stay hydrated, consider probiotics
        3. **Monitoring**: Track your symptoms and menstrual cycle

        **Possible Medications:**
        - For infections: Antifungal cream (if yeast infection suspected)
        - For irregular periods: May need hormonal evaluation
        - Pain management: Ibuprofen 400mg as needed

        **Follow-up needed if:**
        - Symptoms persist beyond 7 days
        - Severe pain or fever
        - Unusual discharge or bleeding

        **Important:** Gynecological health requires proper examination. Please schedule an in-person appointment for accurate diagnosis.

        Do you have any other women's health concerns?
        """
    }
    
    default_response = f"""
    Hello {patient_name},

    Thank you for consulting me about {message.lower()}. As a {specialization}, I've reviewed your symptoms ({symptoms_text}).

    **My Assessment:**
    - Your age ({patient_age}) and symptoms require careful evaluation
    - These concerns fall within my specialty area

    **General Recommendations:**
    1. **Rest and Recovery**: Allow your body time to heal
    2. **Hydration**: Drink plenty of water
    3. **Monitor Symptoms**: Keep track of any changes

    **When to seek immediate care:**
    - If symptoms worsen significantly
    - Development of fever or severe pain
    - Any concerning new symptoms

    **Important:** This virtual consultation cannot replace a physical examination. Please schedule an in-person appointment for proper diagnosis and treatment.

    What other concerns would you like to discuss?
    """
    
    return fallback_responses.get(specialization, default_response)

# API Endpoints
@app.get("/")
async def root():
    return {"message": "Medical Consultation API", "status": "active"}

@app.get("/specializations")
async def get_specializations():
    """Get list of available specializations"""
    return {"specializations": [spec.value for spec in Specialization]}

@app.get("/symptoms/{specialization}")
async def get_symptoms(specialization: Specialization):
    """Get symptoms for a specific specialization"""
    return {"symptoms": SYMPTOMS[specialization]}

@app.post("/register")
async def register_patient(patient: PatientRegistration):
    """Register a new patient"""
    try:
        patient_id = generate_patient_id(patient.name, patient.phone)
        
        patient_data = {
            "id": patient_id,
            "name": patient.name,
            "age": patient.age,
            "gender": patient.gender,
            "phone": patient.phone,
            "medical_history": patient.medical_history,
            "current_medications": patient.current_medications,
            "allergies": patient.allergies,
            "registration_time": datetime.now().isoformat()
        }
        
        patients_db[patient_id] = patient_data
        consultations_db[patient_id] = []
        
        return {
            "message": f"Patient registered successfully! Welcome, {patient.name}!",
            "patient_id": patient_id,
            "status": "success"
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/consult")
async def medical_consultation(request: ConsultationRequest):
    """Handle medical consultation"""
    try:
        # Validate patient exists
        if request.patient_id not in patients_db:
            raise HTTPException(status_code=404, detail="Patient not found. Please register first.")
        
        patient_info = patients_db[request.patient_id]
        
        # Create medical prompt
        prompt = create_medical_prompt(
            patient_info, 
            request.specialization.value, 
            request.selected_symptoms, 
            request.message
        )
        
        # Try to get AI response
        doctor_response = None
        
        # Try Hugging Face first
        if hf_client.api_token != "your_huggingface_token_here":
            doctor_response = hf_client.generate_response(prompt)
        
        # Try IBM Watson if Hugging Face fails
        if not doctor_response and ibm_client.api_key != "your_ibm_api_key_here":
            doctor_response = ibm_client.generate_response(prompt)
        
        # Use fallback if both APIs fail
        if not doctor_response:
            doctor_response = get_fallback_response(
                request.specialization.value,
                request.selected_symptoms,
                request.message,
                patient_info["name"],
                patient_info["age"]
            )
        
        # Store consultation
        consultation = ChatMessage(
            patient_message=request.message,
            doctor_response=doctor_response,
            timestamp=datetime.now().isoformat(),
            symptoms=request.selected_symptoms
        )
        
        consultations_db[request.patient_id].append(consultation)
        
        return ConsultationResponse(
            doctor_response=doctor_response,
            timestamp=consultation.timestamp,
            consultation_id=f"cons_{len(consultations_db[request.patient_id])}"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/patient/{patient_id}/history")
async def get_consultation_history(patient_id: str):
    """Get patient's consultation history"""
    if patient_id not in patients_db:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    return {
        "patient_info": patients_db[patient_id],
        "consultations": consultations_db.get(patient_id, [])
    }

@app.get("/patient/{patient_id}/export")
async def export_consultation_report(patient_id: str):
    """Export consultation report"""
    if patient_id not in patients_db:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    patient_info = patients_db[patient_id]
    consultations = consultations_db.get(patient_id, [])
    
    if not consultations:
        return {"report": "No consultation data to export"}
    
    # Create formatted text report
    report = f"""
╔═══════════════════════════════════════════════════════════════════
║                    MEDICAL CONSULTATION REPORT
╚═══════════════════════════════════════════════════════════════════

📋 PATIENT INFORMATION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Name:                   {patient_info['name']}
Age:                    {patient_info['age']} years
Gender:                 {patient_info['gender']}
Phone:                  {patient_info['phone']}
Registration Date:      {patient_info['registration_time']}

Medical History:        {patient_info.get('medical_history', 'None provided')}
Current Medications:    {patient_info.get('current_medications', 'None')}
Known Allergies:        {patient_info.get('allergies', 'None')}

╔═══════════════════════════════════════════════════════════════════
║                    CONSULTATION HISTORY
╚═══════════════════════════════════════════════════════════════════

"""
    
    # Add each consultation exchange
    for i, consultation in enumerate(consultations, 1):
        symptoms_text = ", ".join(consultation.symptoms) if consultation.symptoms else "None"
        
        report += f"""
┌─────────────────────────────────────────────────────────────────────
│ CONSULTATION #{i} - {consultation.timestamp}
└─────────────────────────────────────────────────────────────────────

👤 PATIENT SYMPTOMS SELECTED:
{symptoms_text}

👤 PATIENT MESSAGE:
{consultation.patient_message}

👨‍⚕️ DOCTOR RESPONSE:
{consultation.doctor_response}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
    
    # Add footer
    report += f"""
╔═══════════════════════════════════════════════════════════════════
║                    REPORT SUMMARY
╚═══════════════════════════════════════════════════════════════════

Total Consultations:    {len(consultations)}
Report Generated:       {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

⚠️  MEDICAL DISCLAIMER:
This virtual consultation is for informational purposes only and does not 
replace professional medical advice, diagnosis, or treatment. Always seek 
the advice of qualified healthcare providers for any medical concerns.

═══════════════════════════════════════════════════════════════════════
                    END OF MEDICAL CONSULTATION REPORT
═══════════════════════════════════════════════════════════════════════
"""
    
    return {"report": report}

@app.delete("/patient/{patient_id}/clear-history")
async def clear_consultation_history(patient_id: str):
    """Clear patient's consultation history"""
    if patient_id not in patients_db:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    consultations_db[patient_id] = []
    return {"message": "Consultation history cleared successfully"}

if __name__ == "__main__":
    import uvicorn
    print("🏥 Starting Medical Consultation API...")
    print("⚠️  Set HUGGINGFACE_API_TOKEN and IBM_API_KEY environment variables for full functionality")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
    # Replace the existing validator imports and Patient class in your main.py

from pydantic import BaseModel, field_validator
from typing import Optional
import re

class Patient(BaseModel):
    name: str
    age: int
    gender: str
    phone: str
    medical_history: Optional[str] = ""
    current_medications: Optional[str] = ""
    allergies: Optional[str] = ""
    
    @field_validator('age')
    @classmethod
    def validate_age(cls, v):
        if v <= 0 or v > 150:
            raise ValueError('Age must be between 1 and 150')
        return v
    
    @field_validator('name', 'phone')
    @classmethod
    def validate_strings(cls, v):
        if not v or not v.strip():
            raise ValueError('This field cannot be empty')
        return v.strip()

class ConsultationRequest(BaseModel):
    specialization: str
    selected_symptoms: list = []
    message: str
    patient_id: str
    
    @field_validator('specialization', 'message', 'patient_id')
    @classmethod
    def validate_required_strings(cls, v):
        if not v or not v.strip():
            raise ValueError('This field cannot be empty')
        return v.strip()
