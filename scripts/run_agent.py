# scripts/run_agent.py
import os
import sys
import json
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

# Add parent directory to sys.path so 'src' can be imported cleanly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.workflow import app
from src.matching_engine import TrialMatchingEngine

# Load environment variables
load_dotenv()

def run_clinical_pipeline(pdf_path: str):
    print("==================================================")
    print("   CLINICAL TRIAL PROTOCOL AGENT PIPELINE         ")
    print("==================================================")
    
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if api_key and api_key.startswith("sk-") and len(api_key) > 10:
        print("[System] Anthropic API Key successfully loaded.")
    else:
        print("[System] Warning: Running in offline/fallback simulation mode.")

    print(f"[System] Target Protocol PDF: {pdf_path}\n")

    initial_state = {
        "trial_id": "NCT_104XB",
        "trial_title": "Phase Protocol 104XB Evaluation",
        "pdf_path": pdf_path,
        "therapeutic_area": "Oncology",
        "extracted_criteria": [],
        "search_results": [],
        "compliance_report": "",
        "messages": [HumanMessage(content=f"Analyze protocol {pdf_path} for trial eligibility criteria.")]
    }
    
    print("=== Phase 1: Running Extraction, Validation & Indexing Workflow ===")
    final_state = app.invoke(initial_state)
    print(f"Workflow completed with compliance status: {final_state.get('compliance_status')}")

    print("\n=== Phase 2: Running AI Patient Matching Engine ===")
    matching_engine = TrialMatchingEngine()
    
    sample_patient = {
        "age": 50,
        "diagnosis": "Solid tumor malignancy",
        "metastases": "None active",
        "autoimmune_history": "None"
    }

    match_result = matching_engine.evaluate_patient_fit(sample_patient, trial_id="NCT_104XB")
    print("\n--- Patient Eligibility Evaluation Result ---")
    print(json.dumps(match_result, indent=2))

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run Clinical Trial Protocol Agent pipeline.")
    parser.add_argument(
        "--pdf", 
        type=str, 
        default="data/protocols/trial_protocol_104xb.pdf",
        help="Path to the clinical trial protocol PDF file."
    )
    args = parser.parse_args()
    
    run_clinical_pipeline(args.pdf)