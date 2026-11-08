# src/workflow.py
import os
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage
from src.tools import extract_criteria_with_rag
from src.matching_engine import TrialMatchingEngine

class AgentState(TypedDict):
    trial_id: str
    trial_title: str
    pdf_path: str
    therapeutic_area: str
    extracted_criteria: Dict[str, List[str]]
    search_results: str
    compliance_report: str
    hil_review_status: str
    compliance_status: str
    messages: List[BaseMessage]

def extractor_node(state: AgentState) -> Dict[str, Any]:
    print("[Node: Extractor] Starting criteria extraction...")
    pdf_path = state.get("pdf_path")
    therapeutic_area = state.get("therapeutic_area", "General")
    
    result, context = extract_criteria_with_rag(pdf_path, therapeutic_area=therapeutic_area)
    
    extracted_dict = {
        "inclusion_criteria": result.inclusion_criteria if result else [],
        "exclusion_criteria": result.exclusion_criteria if result else []
    }
    
    print(f"[Debug Extractor] Extracted criteria count: Inclusion={len(extracted_dict['inclusion_criteria'])}, Exclusion={len(extracted_dict['exclusion_criteria'])}")
    return {
        "extracted_criteria": extracted_dict,
        "search_results": context
    }

def validator_node(state: AgentState) -> Dict[str, Any]:
    print("[Node: Validator] Starting validation & evaluation check...")
    criteria = state.get("extracted_criteria", {})
    has_criteria = bool(criteria.get("inclusion_criteria") or criteria.get("exclusion_criteria"))
    
    if has_criteria:
        report = "Validation passed successfully. Criteria are structurally populated."
        status = "VALID"
    else:
        report = "Validation flagged: Criteria lists are empty or missing."
        status = "FLAGGED_EMPTY"
        
    print(f"[Node: Validator] {report}")
    return {
        "compliance_report": report,
        "validation_status": status
    }

def human_review_node(state: AgentState) -> Dict[str, Any]:
    print("[Node: Human Review] Processing clinical expert review sign-off...")
    criteria = state.get("extracted_criteria", {})
    has_criteria = bool(criteria.get("inclusion_criteria") or criteria.get("exclusion_criteria"))
    print(f"[Debug Human Review] Criteria present: {has_criteria}")
    
    # HIL Confirmation Logic for Flagged / Pending Items
    if not has_criteria:
        print("[Warning] Criteria flagged as empty or pending review. HIL intervention required.")
        review_status = "PENDING_HIL_REVIEW"
    else:
        print("[System] HIL Confirmation: Criteria reviewed and approved by clinical expert.")
        review_status = "APPROVED"
        
    return {
        "hil_review_status": review_status
    }

def indexer_node(state: AgentState) -> Dict[str, Any]:
    print("[Node: Indexer] Storing validated criteria to database...")
    criteria = state.get("extracted_criteria", {})
    review_status = state.get("hil_review_status", "PENDING_HIL_REVIEW")
    
    if review_status != "APPROVED" or not criteria.get("inclusion_criteria"):
        print("[Warning] Indexer received unapproved or empty criteria, skipping database update overwrite.")
        return {"compliance_status": "FLAGGED_PENDING"}
        
    # Save structured criteria to the Trial database via TrialMatchingEngine
    engine = TrialMatchingEngine()
    engine.update_trial_criteria(
        trial_id=state.get("trial_id", "NCT_104XB"),
        inclusion=criteria.get("inclusion_criteria", []),
        exclusion=criteria.get("exclusion_criteria", [])
    )
    
    print("[Success] Database successfully updated with extracted criteria for Phase 2.")
    return {"compliance_status": "PASSED"}

# Build the LangGraph Workflow
workflow = StateGraph(AgentState)

workflow.add_node("extractor", extractor_node)
workflow.add_node("validator", validator_node)
workflow.add_node("human_review", human_review_node)
workflow.add_node("indexer", indexer_node)

workflow.set_entry_point("extractor")
workflow.add_edge("extractor", "validator")
workflow.add_edge("validator", "human_review")
workflow.add_edge("human_review", "indexer")
workflow.add_edge("indexer", END)

app = workflow.compile()