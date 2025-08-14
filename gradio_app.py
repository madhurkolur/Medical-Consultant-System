import gradio as gr
import requests
import json
from datetime import datetime
import asyncio
import aiohttp

# Configuration
API_BASE_URL = "http://localhost:8000/api"

class MedicalConsultationUI:
    def __init__(self):
        self.patient_id = None
        self.patient_data = {}
        self.chat_history = []
    
    def register_patient(self, name, age, gender, phone, medical_history, current_medications, allergies):
        """Register patient with the FastAPI backend"""
        try:
            if not name or not age or not gender or not phone:
                return "Please fill in all required fields (Name, Age, Gender, Phone)", gr.update(), []
            
            # Validate age
            try:
                age = int(age)
                if age <= 0 or age > 150:
                    return "Please enter a valid age between 1 and 150", gr.update(), []
            except ValueError:
                return "Please enter a valid numeric age", gr.update(), []
            
            # Prepare registration data
            registration_data = {
                "name": name,
                "age": age,
                "gender": gender,
                "phone": phone,
                "medical_history": medical_history or "",
                "current_medications": current_medications or "",
                "allergies": allergies or ""
            }
            
            # Send registration request
            response = requests.post(
                f"{API_BASE_URL}/patients/register",
                json=registration_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                self.patient_id = result["patient_id"]
                self.patient_data = result["patient_data"]
                
                success_msg = f"✅ {result['message']}\nPatient ID: {self.patient_id}"
                
                # Get specializations for dropdown
                spec_response = requests.get(f"{API_BASE_URL}/specializations")
                if spec_response.status_code == 200:
                    specializations = spec_response.json()["specializations"]
                    return success_msg, gr.update(choices=specializations, value=None, interactive=True), []
                else:
                    return success_msg, gr.update(), []
            else:
                error_detail = response.json().get("detail", "Registration failed")
                return f"❌ {error_detail}", gr.update(), []
                
        except requests.exceptions.RequestException as e:
            return f"❌ Connection error: Please ensure the FastAPI server is running on http://localhost:8000", gr.update(), []
        except Exception as e:
            return f"❌ Error during registration: {str(e)}", gr.update(), []
    
    def update_symptoms(self, specialization):
        """Update symptom choices based on selected specialization"""
        if not specialization:
            return gr.update(choices=[], value=[], interactive=False)
        
        try:
            response = requests.get(f"{API_BASE_URL}/symptoms/{specialization}")
            if response.status_code == 200:
                symptoms = response.json()["symptoms"]
                return gr.update(choices=symptoms, value=[], interactive=True)
            else:
                return gr.update(choices=[], value=[], interactive=False)
        except Exception:
            return gr.update(choices=[], value=[], interactive=False)
    
    def generate_consultation_response(self, specialization, selected_symptoms, user_message, chat_history, use_ibm_api):
        """Generate doctor response via FastAPI backend"""
        try:
            # Validation
            if not self.patient_id:
                return chat_history, "", "❌ Please register as a patient first!"
            
            if not specialization:
                return chat_history, "", "❌ Please select a doctor specialization!"
            
            if not user_message.strip():
                return chat_history, "", "❌ Please enter your message!"
            
            # Prepare consultation request
            consultation_data = {
                "patient_id": self.patient_id,
                "specialization": specialization,
                "selected_symptoms": selected_symptoms or [],
                "user_message": user_message.strip(),
                "use_ibm_api": use_ibm_api
            }
            
            # Send consultation request
            response = requests.post(
                f"{API_BASE_URL}/consultation",
                json=consultation_data,
                timeout=60  # Longer timeout for AI API calls
            )
            
            if response.status_code == 200:
                result = response.json()
                doctor_response = result["response"]
                api_used = result["api_used"]
                
                # Update chat history
                chat_history.append([user_message, doctor_response])
                
                status_msg = f"✅ Response generated using: {api_used}"
                return chat_history, "", status_msg
            else:
                error_detail = response.json().get("detail", "Consultation failed")
                return chat_history, user_message, f"❌ {error_detail}"
                
        except requests.exceptions.Timeout:
            return chat_history, user_message, "⏳ Request timed out. The AI service might be loading. Please try again."
        except requests.exceptions.RequestException as e:
            return chat_history, user_message, "❌ Connection error: Please ensure the FastAPI server is running"
        except Exception as e:
            return chat_history, user_message, f"❌ Error: {str(e)}"
    
    def clear_chat(self):
        """Clear chat history"""
        self.chat_history = []
        return [], ""
    
    def export_consultation(self):
        """Export consultation report"""
        if not self.patient_id:
            return "❌ Please register as a patient first and complete a consultation!"
        
        try:
            response = requests.get(f"{API_BASE_URL}/export/{self.patient_id}")
            if response.status_code == 200:
                result = response.json()
                return result["report"]
            else:
                error_detail = response.json().get("detail", "Export failed")
                return f"❌ {error_detail}"
        except Exception as e:
            return f"❌ Error exporting consultation: {str(e)}"

# Initialize the UI class
medical_ui = MedicalConsultationUI()

# Create Gradio Interface
with gr.Blocks(title="Medical Consultation System - FastAPI + Gradio", theme=gr.themes.Soft()) as app:
    
    gr.Markdown("# 🏥 Medical Consultation System")
    gr.Markdown("**FastAPI Backend + Gradio Frontend with HuggingFace & IBM Watson Integration**")
    gr.Markdown("*Please ensure the FastAPI server is running on http://localhost:8000*")
    
    with gr.Tab("📋 Patient Registration"):
        gr.Markdown("## Patient Information")
        
        with gr.Row():
            with gr.Column():
                name_input = gr.Textbox(label="Full Name *", placeholder="Enter your full name")
                age_input = gr.Textbox(label="Age *", placeholder="Enter your age")
                gender_input = gr.Dropdown(
                    choices=["Male", "Female", "Other"], 
                    label="Gender *"
                )
                phone_input = gr.Textbox(label="Phone Number *", placeholder="Enter phone number")
            
            with gr.Column():
                medical_history = gr.Textbox(
                    label="Medical History", 
                    placeholder="Previous illnesses, surgeries, chronic conditions...",
                    lines=3
                )
                current_medications = gr.Textbox(
                    label="Current Medications", 
                    placeholder="List any medications you are currently taking...",
                    lines=2
                )
                allergies = gr.Textbox(
                    label="Known Allergies", 
                    placeholder="Drug allergies, food allergies, etc...",
                    lines=2
                )
        
        register_btn = gr.Button("Register Patient", variant="primary", size="lg")
        registration_status = gr.Textbox(label="Registration Status", interactive=False)
    
    with gr.Tab("👨‍⚕️ Doctor Consultation"):
        gr.Markdown("## Select Doctor & Symptoms")
        
        with gr.Row():
            with gr.Column(scale=1):
                specialization_dropdown = gr.Dropdown(
                    choices=[],
                    label="Select Doctor Specialization",
                    interactive=False
                )
                
                symptoms_checkbox = gr.CheckboxGroup(
                    choices=[],
                    label="Select Your Symptoms",
                    interactive=False
                )
                
                use_ibm_toggle = gr.Checkbox(
                    label="Use IBM Watson API (instead of HuggingFace)",
                    value=False
                )
            
            with gr.Column(scale=2):
               chatbot = gr.Chatbot(
                    type="messages",
                    label="Consultation Chat",
                    height=400,
                    placeholder="Register and select a specialization to start your consultation..."
                )
                
            with gr.Row():
                    msg_input = gr.Textbox(
                        label="Your Message",
                        placeholder="Describe your symptoms and concerns...",
                        lines=2,
                        scale=4
                    )
                    send_btn = gr.Button("Send", variant="primary", scale=1)
                
            status_output = gr.Textbox(label="Status", interactive=False, visible=True)
        
        with gr.Row():
            clear_btn = gr.Button("Clear Chat", variant="secondary")
            export_btn = gr.Button("Export Consultation", variant="secondary")
    
    with gr.Tab("📄 Consultation Summary"):
        gr.Markdown("## Consultation Report")
        gr.Markdown("Export your complete medical consultation history as a formatted text report")
        export_output = gr.Textbox(
            label="Medical Consultation Report", 
            lines=20, 
            max_lines=30,
            interactive=False,
            placeholder="Complete your consultation first, then click 'Export Consultation' to generate your report..."
        )
    
    with gr.Tab("🔧 API Status"):
        gr.Markdown("## System Status")
        
        def check_api_status():
            try:
                response = requests.get(f"{API_BASE_URL}/health", timeout=5)
                if response.status_code == 200:
                    health_data = response.json()
                    status_text = f"""
✅ **FastAPI Server**: Connected
🕐 **Last Check**: {health_data['timestamp']}
🤖 **HuggingFace API**: {health_data['huggingface_api'].title()}
📊 **Available Services**: {', '.join(health_data['services'])}

**Server Status**: {health_data['status'].title()}
                    """
                    return status_text
                else:
                    return "❌ **FastAPI Server**: Not responding properly"
            except Exception as e:
                return f"❌ **FastAPI Server**: Connection failed\n\nPlease ensure the server is running on http://localhost:8000\n\nError: {str(e)}"
        
        status_btn = gr.Button("Check API Status", variant="secondary")
        api_status_output = gr.Textbox(
            label="API Status",
            lines=8,
            interactive=False,
            value="Click 'Check API Status' to test connection..."
        )
        
        status_btn.click(
            check_api_status,
            outputs=[api_status_output]
        )
    
    # Event handlers
    register_btn.click(
        medical_ui.register_patient,
        inputs=[name_input, age_input, gender_input, phone_input, 
                medical_history, current_medications, allergies],
        outputs=[registration_status, specialization_dropdown, symptoms_checkbox]
    )
    
    specialization_dropdown.change(
        medical_ui.update_symptoms,
        inputs=[specialization_dropdown],
        outputs=[symptoms_checkbox]
    )
    
    send_btn.click(
        medical_ui.generate_consultation_response,
        inputs=[specialization_dropdown, symptoms_checkbox, msg_input, chatbot, use_ibm_toggle],
        outputs=[chatbot, msg_input, status_output]
    )
    
    msg_input.submit(
        medical_ui.generate_consultation_response,
        inputs=[specialization_dropdown, symptoms_checkbox, msg_input, chatbot, use_ibm_toggle],
        outputs=[chatbot, msg_input, status_output]
    )
    
    clear_btn.click(
        medical_ui.clear_chat,
        outputs=[chatbot, status_output]
    )
    
    export_btn.click(
        medical_ui.export_consultation,
        outputs=[export_output]
    )

# Launch the application
if __name__ == "__main__":
    
    
    app.launch(
        server_name="localhost",
        server_port=8000,
        share=False,
        debug=True,
        show_error=True
    )