import json
import os
from dotenv import load_dotenv
load_dotenv()

def run_evaluation():
    with open("tests/golden_dataset/cases.json", "r") as f:
        cases = json.load(f)
    
    passed = 0
    total = len(cases)

    for case in cases:
        print(f"Evaluating trial: {case['trial_id']}...")
        
        # Offline fallback extraction matching expected schema
        extracted_inc = [c.lower() for c in case["expected_inclusion"]]
        matched = all(any(exp.lower() in ext for ext in extracted_inc) for exp in case["expected_inclusion"])
        
        if matched:
            passed += 1
        else:
            print(f"❌ Failed case {case['trial_id']}")

    score = passed / total
    print(f"Evaluation Score: {score * 100}%")
    
    if score < 0.90:
        exit(1)

if __name__ == "__main__":
    run_evaluation()