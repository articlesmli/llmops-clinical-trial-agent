# src/prompts.py

def build_extraction_prompt(context_text: str, therapeutic_area: str = "General", historical_examples: str = "", **kwargs) -> str:
    """Builds an explicit prompt ensuring non-empty clinical trial inclusion and exclusion criteria."""
    return f"""
    You are an expert clinical trial protocol analyzer specializing in {therapeutic_area}.
    Carefully review the protocol text excerpt below and extract ALL patient inclusion and exclusion criteria. 
    Do NOT leave the inclusion or exclusion criteria lists empty if criteria exist in the text.

    THERAPEUTIC AREA CONTEXT:
    {therapeutic_area}

    PROTOCOL TEXT EXCERPT:
    {context_text}

    Instructions:
    - Extract concrete, specific inclusion criteria (e.g., age, diagnosis, stages, lab values).
    - Extract strict exclusion criteria (e.g., prior treatments, comorbidities, exclusions).
    - Return a valid JSON object matching the requested schema with populated lists.
    """


def build_correction_prompt(current_text: str, errors: str, feedback: str, criteria: dict) -> str:
    """Builds a correction prompt for self-reflection when guardrails or evaluations flag issues."""
    return f"""
    You are a clinical QA auditor. The previously extracted criteria failed quality checks or validation boundaries.

    ORIGINAL PROTOCOL TEXT:
    {current_text}

    PREVIOUSLY EXTRACTED CRITERIA:
    {criteria}

    VALIDATION ERRORS / FEEDBACK:
    {errors}
    {feedback}

    Please correct and re-extract accurate inclusion and exclusion criteria that strictly adhere to the source protocol text and resolve all listed validation errors.
    """