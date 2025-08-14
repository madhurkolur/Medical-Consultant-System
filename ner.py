from transformers import pipeline
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore")

def load_medical_ner_model():
    """Load the medical NER model"""
    try:
        print("Loading medical NER model...")
        ner_pipeline = pipeline("ner", model="samant/medical-ner")
        print("Model loaded successfully!")
        return ner_pipeline
    except Exception as e:
        print(f"Error loading model: {e}")
        return None

def extract_medical_entities(text, ner_pipeline):
    """Extract medical entities from text"""
    try:
        entities = ner_pipeline(text)
        return entities
    except Exception as e:
        print(f"Error processing text: {e}")
        return []

def display_entities(entities, text):
    """Display extracted entities in a readable format"""
    print("\n" + "="*50)
    print("MEDICAL ENTITY EXTRACTION RESULTS")
    print("="*50)
    print(f"Input text: {text}")
    print("\nExtracted entities:")
    
    if not entities:
        print("No entities found.")
        return
    
    # Group entities by label
    entity_groups = {}
    for entity in entities:
        label = entity['entity']
        if label not in entity_groups:
            entity_groups[label] = []
        entity_groups[label].append(entity)
    
    for label, group in entity_groups.items():
        print(f"\n{label}:")
        for entity in group:
            word = entity['word']
            confidence = entity['score']
            print(f"  - {word} (confidence: {confidence:.3f})")

def main():
    # Load the model
    ner_pipeline = load_medical_ner_model()
    
    if ner_pipeline is None:
        print("Failed to load model. Exiting.")
        return
    
    # Example texts for testing
    sample_texts = [
        "The patient has been diagnosed with Type 2 Diabetes and prescribed Metformin.",
        "Patient presents with hypertension and was given Lisinopril 10mg daily.",
        "The MRI showed a small lesion in the frontal lobe. Recommend follow-up CT scan.",
        "Patient has a history of myocardial infarction and is on aspirin therapy."
    ]
    
    # Process each sample text
    for i, text in enumerate(sample_texts, 1):
        print(f"\n{'='*20} EXAMPLE {i} {'='*20}")
        entities = extract_medical_entities(text, ner_pipeline)
        display_entities(entities, text)
    
    # Interactive mode
    print(f"\n{'='*20} INTERACTIVE MODE {'='*20}")
    print("Enter your own medical text (or 'quit' to exit):")
    
    while True:
        user_text = input("\nEnter text: ").strip()
        
        if user_text.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break
        
        if not user_text:
            print("Please enter some text.")
            continue
        
        entities = extract_medical_entities(user_text, ner_pipeline)
        display_entities(entities, user_text)

if __name__ == "__main__":
    main()
    