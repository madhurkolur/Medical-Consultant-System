# frontend_client.py - Gradio Frontend Client
import gradio as gr
import requests
from datetime import datetime
import json

# FastAPI backend configuration
API_BASE_URL = "http://localhost:8000"  # Change this to your FastAPI server URL

# Global variables to store session data
current_patient_id = None
current_specializations = []
current_symptoms = {}

class APIClient:
    """Client to interact with FastAPI backend"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    def register_patient(self, patient_data: dict):
        """Register a patient"""
        try:
            response = requests.post(f"{self.base_url}/register", json=patient_data)
            if response.status_code == 200:
                return response.json(), None
            else:
                return None, response.json().get("detail", "Registration failed")
        except Exception as e:
            return None, f"Connection error: {str(e)}"
    
    def get_specializations(self):
        """Get list of specializations"""
        try:
            response = requests.get(f"{self.base_url}/specializations")
            if response.status_code == 200:
                return response.json().get("specializations", []), None
            else:
                return [], "Failed to load specializations"
        except Exception as e:
            return [], f"Connection error: {str(e)}"
    
    def get_symptoms(self, specialization: str):
        """Get symptoms for a specialization"""
        try:
            response = requests.get(f"{self.base_url}/symptoms/{specialization}")
            if response.status_code == 200:
                return response.json().get("symptoms", []), None
            else:
                return [], "Failed to load symptoms"
        except Exception as e:
            return [], f"Connection error: {str(e)}"
    
    def send_consultation(self, consultation_data: dict):
        """Send consultation request"""
        try:
            response = requests.post(f"{self.base_url}/consult", json=consultation_data)
            if response.status_code == 200:
                return response.json(), None
            else:
                return None, response.json().get("detail", "Consultation failed")
        except Exception as e:
            return None, f"Connection error: {str(e)}"
    
    def get_consultation_history(self, patient_id: str):
        """Get patient's consultation history"""
        try:
            response = requests.get(f"{self.base_url}/patient/{patient_id}/history")
            if response.status_code == 200:
                return response.json(), None
            else:
                return None, response.json().get("detail", "Failed to get history")
        except Exception as e:
            return None, f"Connection error: {str(e)}"
    
    def export_consultation_report(self, patient_id: str):
        """Export consultation report"""
        try:
            response = requests.get(f"{self.base_url}/patient/{patient_id}/export")
            if response.status_code == 200:
                return response.json().get("report", ""), None
            else:
                return "", response.json().get("detail", "Export failed")
        except Exception as e:
            return "", f"Connection error: {str(e)}"
    
    def clear_consultation_history(self, patient_id: str):
        """Clear patient's consultation history"""
        try:
            response = requests.delete(f"{self.base_url}/patient/{patient_id}/clear-history")
            if response.status_code == 200:
                return response.json().get("message", "History cleared"), None
            else:
                return "", response.json().get("detail", "Clear failed")
        except Exception as e:
            return "", f"Connection error: {str(e)}"

# Initialize API client
api_client = APIClient(API_BASE_URL)

def register_patient(name, age, gender, phone, medical_history, current_medications, allergies):
    """Register patient with the backend API"""
    global current_patient_id, current_specializations
    
    if not name or not age or not gender or not phone:
        return "Please fill in all required fields (Name, Age, Gender, Phone)", "", []
    
    try:
        age = int(age)
        if age <= 0 or age > 150:
            return "Please enter a valid age between 1 and 150", "", []
    except:
        return "Please enter a valid age", "", []
    
    patient_data = {
        "name": name,
        "age": age,
        "gender": gender,
        "phone": phone,
        "medical_history": medical_history or "",
        "current_medications": current_medications or "",
        "allergies": allergies or ""
    }
    
    result, error = api_client.register_patient(patient_data)
    
    if error:
        return f"❌ Registration failed: {error}", "", []
    
    # Store patient ID and load specializations
    current_patient_id = result["patient_id"]
    specializations, spec_error = api_client.get_specializations()
    
    if spec_error:
        success_msg = f"✅ {result['message']}\n⚠️ Warning: {spec_error}"
        return success_msg, "", []
    
    current_specializations = specializations
    success_msg = f"✅ {result['message']}\nYou can now select a doctor specialization and symptoms."
    
    return success_msg, gr.update(choices=specializations, value=None, interactive=True), []

def update_symptoms(specialization):
    """Update symptom checkboxes based on selected specialization"""
    global current_symptoms
    
    if not specialization:
        return gr.update(choices=[], value=[], interactive=False)
    
    symptoms, error = api_client.get_symptoms(specialization)
    
    if error:
        return gr.update(choices=[], value=[], interactive=False, info=f"Error: {error}")
    
    current_symptoms[specialization] = symptoms
    return gr.update(choices=symptoms, value=[], interactive=True)

def generate_doctor_response(specialization, selected_symptoms, user_message, chat_history):
    """Generate doctor response using the backend API"""
    global current_patient_id
    
    # Validation checks
    if not current_patient_id:
        return chat_history, "", "❌ Please register as a patient first!"
    
    if not specialization:
        return chat_history, "", "❌ Please select a doctor specialization!"
    
    if not user_message.strip():
        return chat_history, "", "❌ Please enter your message!"
    
    # Prepare consultation request
    consultation_data = {
        "specialization": specialization,
        "selected_symptoms": selected_symptoms or [],
        "message": user_message.strip(),
        "patient_id": current_patient_id
    }
    
    result, error = api_client.send_consultation(consultation_data)
    
    if error:
        return chat_history, "", f"❌ Consultation failed: {error}"
    
    # Add to chat history for display
    doctor_response = result["doctor_response"]
    chat_history.append([user_message, doctor_response])
    
    success_msg = "✅ Response received from doctor"
    if "fallback" in doctor_response.lower() or len(doctor_response) < 100:
        success_msg += "\n⚠️ Using demo mode - Configure API keys for enhanced responses"
    
    return chat_history, "", success_msg

def clear_chat():
    """Clear the chat history"""
    global current_patient_id
    
    if not current_patient_id:
        return [], "❌ No active patient session"
    
    message, error = api_client.clear_consultation_history(current_patient_id)
    
    if error:
        return [], f"❌ Error clearing history: {error}"
    
    return [], "✅ Chat history cleared successfully"

def export_consultation():
    """Export consultation history as formatted text"""
    global current_patient_id
    
    if not current_patient_id:
        return "❌ No active patient session. Please register first."
    
    report, error = api_client.export_consultation_report(current_patient_id)
    
    if error:
        return f"❌ Export failed: {error}"
    
    if not report or report == "No consultation data to export":
        return "ℹ️ No consultation data to export. Complete your consultation first."
    
    return report

def load_consultation_history():
    """Load and display consultation history"""
    global current_patient_id
    
    if not current_patient_id:
        return "❌ No active patient session. Please register first."
    
    history_data, error = api_client.get_consultation_history(current_patient_id)
    
    if error:
        return f"❌ Failed to load history: {error}"
    
    if not history_data or not history_data.get("consultations"):
        return "ℹ️ No consultation history found."
    
    # Format the history for display
    formatted_history = ""
    for consultation in history_data["consultations"]:
        timestamp = consultation.get("timestamp", "Unknown time")
        specialization = consultation.get("specialization", "Unknown")
        symptoms = consultation.get("symptoms", [])
        message = consultation.get("message", "")
        response = consultation.get("doctor_response", "")
        
        formatted_history += f"**Consultation on {timestamp}**\n"
        formatted_history += f"**Specialization:** {specialization}\n"
        if symptoms:
            formatted_history += f"**Symptoms:** {', '.join(symptoms)}\n"
        formatted_history += f"**Your Message:** {message}\n"
        formatted_history += f"**Doctor Response:** {response}\n"
        formatted_history += "\n" + "="*50 + "\n\n"
    
    return formatted_history

def check_api_connection():
    """Check if the FastAPI backend is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=5)
        if response.status_code == 200:
            return "🟢 Backend API is running"
        else:
            return "🟡 Backend API returned unexpected status"
    except requests.exceptions.ConnectionError:
        return "🔴 Backend API is not running. Please start the FastAPI server."
    except Exception as e:
        return f"🟡 API connection issue: {str(e)}"

# Create Gradio Interface
with gr.Blocks(title="Medical Consultation System", theme=gr.themes.Soft()) as app:
    
    gr.Markdown("# 🏥 Medical Consultation System")
    gr.Markdown("Connect with specialized doctors for professional medical consultation")
    
    # API Status indicator
    with gr.Row():
        api_status = gr.Textbox(
            label="API Connection Status",
            value=check_api_connection(),
            interactive=False,
            container=True
        )
        refresh_status_btn = gr.Button("🔄 Refresh Status", size="sm")
    
    with gr.Tab("📋 Patient Registration"):
        gr.Markdown("## Patient Information")
        gr.Markdown("*Required fields are marked with *")
        
        with gr.Row():
            with gr.Column():
                name_input = gr.Textbox(label="Full Name *", placeholder="Enter your full name")
                age_input = gr.Textbox(label="Age *", placeholder="Enter your age")
                gender_input = gr.Dropdown(
                    choices=["Male", "Female", "Other"], 
                    label="Gender *"
                )
                phone_input = gr.Textbox(label="Phone Number *", placeholder="Enter your phone number")
            
            with gr.Column():
                medical_history_input = gr.Textbox(
                    label="Medical History (Optional)", 
                    placeholder="Any previous medical conditions, surgeries, etc.",
                    lines=3
                )
                current_medications_input = gr.Textbox(
                    label="Current Medications (Optional)", 
                    placeholder="List any medications you are currently taking",
                    lines=3
                )
                allergies_input = gr.Textbox(
                    label="Allergies (Optional)", 
                    placeholder="Any known allergies to medications, foods, etc.",
                    lines=2
                )
        
        register_btn = gr.Button("📝 Register Patient", variant="primary", size="lg")
        registration_status = gr.Textbox(
            label="Registration Status", 
            interactive=False,
            lines=2
        )
    
    with gr.Tab("👩‍⚕️ Medical Consultation"):
        gr.Markdown("## Consult with a Doctor")
        gr.Markdown("Select a specialization and describe your symptoms to get professional medical advice")
        
        with gr.Row():
            with gr.Column(scale=1):
                specialization_dropdown = gr.Dropdown(
                    choices=[],
                    label="Select Doctor Specialization",
                    interactive=False
                )
                
                symptoms_checklist = gr.CheckboxGroup(
                    choices=[],
                    label="Select Relevant Symptoms (Optional)",
                    interactive=False
                )
                
                gr.Markdown("### Additional Information")
                user_message_input = gr.Textbox(
                    label="Describe your condition",
                    placeholder="Please describe your symptoms, concerns, or questions in detail...",
                    lines=4
                )
                
                with gr.Row():
                    send_btn = gr.Button("💬 Send Message", variant="primary")
                    clear_btn = gr.Button("🗑️ Clear Chat", variant="secondary")
            
            with gr.Column(scale=2):
                chatbot = gr.Chatbot(
                    label="Medical Consultation Chat",
                    height=500,
                    show_label=True
                )
                
                consultation_status = gr.Textbox(
                    label="Status",
                    interactive=False,
                    lines=2
                )
    
    with gr.Tab("📊 Consultation History"):
        gr.Markdown("## Your Consultation History")
        gr.Markdown("View and export your previous medical consultations")
        
        with gr.Row():
            load_history_btn = gr.Button("📋 Load History", variant="primary")
            export_btn = gr.Button("📄 Export Report", variant="secondary")
        
        history_display = gr.Textbox(
            label="Consultation History",
            lines=20,
            interactive=False,
            placeholder="Click 'Load History' to view your consultation records..."
        )
        
        export_display = gr.Textbox(
            label="Exported Report",
            lines=10,
            interactive=False,
            placeholder="Click 'Export Report' to generate a formatted consultation report..."
        )
    
    with gr.Tab("ℹ️ About"):
        gr.Markdown("""
        ## About Medical Consultation System
        
        This system provides AI-powered medical consultations across various specializations.
        
        ### Features:
        - 🏥 **Multiple Specializations**: Cardiology, Dermatology, Orthopedics, Neurology, and more
        - 💊 **Symptom-based Consultations**: Select relevant symptoms for more accurate advice
        - 📋 **Patient Registration**: Secure patient information management
        - 💬 **Interactive Chat**: Real-time consultation with AI doctors
        - 📊 **Consultation History**: Track and export your medical consultations
        - 🔒 **Privacy Focused**: Your data is handled securely
        
        ### How to Use:
        1. **Register**: Fill in your patient information in the Registration tab
        2. **Consult**: Select a specialization and describe your symptoms
        3. **Chat**: Interact with the AI doctor for personalized advice
        4. **Review**: Check your consultation history and export reports
        
        ### Important Disclaimer:
        ⚠️ **This system provides general medical information and should not replace professional medical advice, diagnosis, or treatment. Always consult with qualified healthcare providers for serious medical concerns.**
        
        ### Technical Requirements:
        - FastAPI backend server running on `http://localhost:8000`
        - Internet connection for API calls
        - Modern web browser with JavaScript enabled
        """)
    
    # Event handlers
    refresh_status_btn.click(
        fn=check_api_connection,
        outputs=[api_status]
    )
    
    register_btn.click(
        fn=register_patient,
        inputs=[
            name_input,
            age_input,
            gender_input,
            phone_input,
            medical_history_input,
            current_medications_input,
            allergies_input
        ],
        outputs=[
            registration_status,
            specialization_dropdown,
            symptoms_checklist
        ]
    )
    
    specialization_dropdown.change(
        fn=update_symptoms,
        inputs=[specialization_dropdown],
        outputs=[symptoms_checklist]
    )
    
    send_btn.click(
        fn=generate_doctor_response,
        inputs=[
            specialization_dropdown,
            symptoms_checklist,
            user_message_input,
            chatbot
        ],
        outputs=[
            chatbot,
            user_message_input,
            consultation_status
        ]
    )
    
    clear_btn.click(
        fn=clear_chat,
        outputs=[chatbot, consultation_status]
    )
    
    load_history_btn.click(
        fn=load_consultation_history,
        outputs=[history_display]
    )
    
    export_btn.click(
        fn=export_consultation,
        outputs=[export_display]
    )

# Launch the application
if __name__ == "__main__":
    print("🏥 Starting Medical Consultation System...")
    print(f"🔗 API Backend: {API_BASE_URL}")
    print("🌐 Launching Gradio interface...")
    
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        show_error=True,
        share=False,
        inbrowser=True
    )