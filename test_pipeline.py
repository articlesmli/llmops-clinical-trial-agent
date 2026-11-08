import os
from dotenv import load_dotenv
load_dotenv()

from src.guardrails import ProtocolGuardrails
from src.evaluation import ProductionEvaluator

def test_guardrails():
    print("--- Testing Guardrails ---")
    dirty_text = "  Patient must have normal ECG \x00 with no prior history...  "
    clean_text = ProtocolGuardrails.sanitize_input_text(dirty_text)
    print(f"Sanitized input: '{clean_text}'")

    safe_criteria = ["Age >= 18 years", "Confirmed diagnosis of Type 2 Diabetes"]
    unsafe_criteria = ["Guaranteed 100% cure-all therapy", "Age >= 18"]
    
    print("Safe criteria check:", ProtocolGuardrails.validate_clinical_boundaries(safe_criteria))
    print("Unsafe criteria check:", ProtocolGuardrails.validate_clinical_boundaries(unsafe_criteria))

def test_evaluator():
    print("\n--- Testing Production Evaluator ---")
    evaluator = ProductionEvaluator()
    source_text = "Inclusion Criteria: Age >= 18 years, advanced solid tumors."
    extracted = {"inclusion_criteria": ["Age >= 18 years", "Advanced solid tumors"]}
    
    result = evaluator.evaluate_faithfulness(source_text, extracted)
    print(f"Evaluator result: {result}")

if __name__ == "__main__":
    test_guardrails()
    test_evaluator()
    print("\n✅ Guardrails and evaluation components loaded and ready!")