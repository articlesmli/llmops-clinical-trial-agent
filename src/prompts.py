# src/prompts.py

def build_extraction_prompt(context_text: str, therapeutic_area: str = "General", historical_examples: str = "", **kwargs) -> str:
    """Builds a robust dynamic prompt for extracting clinical trial inclusion and exclusion criteria."""
    return f"""
    You are an expert clinical trial protocol analyzer specializing in {therapeutic_area}.
    Review the protocol text below and extract clear, structured patient inclusion and exclusion criteria.

    THERAPEUTIC AREA CONTEXT:
    {therapeutic_area}

    HISTORICAL GUIDANCE/EXAMPLES:
    {historical_examples if historical_examples else "None provided."}

    PROTOCOL TEXT EXCERPT:
    {context_text}

    Instructions:
    - Extract specific, measurable inclusion criteria (e.g., age ranges, confirmed diagnoses, lab thresholds).
    - Extract strict exclusion criteria (e.g., prior treatments, comorbidities, contraindications).
    - Return output matching the requested schema.
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