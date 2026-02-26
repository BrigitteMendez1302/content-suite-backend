"""JSON extraction utilities for LLM model outputs."""
import json
import re
from typing import Any


def extract_json(text: str) -> Any:
    """Extract JSON object from LLM text output with best-effort parsing.

    Handles common LLM output formatting issues:
    - Strips markdown code fences (```json, ```), etc.)
    - Attempts direct JSON parsing first
    - Falls back to regex-based object extraction
    - Extracts first {...} block if present

    Args:
        text: Raw text output from LLM (may contain markdown, extra text, etc.).

    Returns:
        Parsed JSON object/array/scalar value.

    Raises:
        ValueError: If no valid JSON object can be extracted or parsed.

    Examples:
        >>> extract_json('```json {"status": "ok"} ```')
        {'status': 'ok'}

        >>> extract_json('Here is data: {"id": 123} and more text')
        {'id': 123}

        >>> extract_json('invalid json')
        ValueError: No JSON object found in LLM output.
    """
    cleaned = re.sub(r"```(json)?", "", text, flags=re.IGNORECASE).replace("```", "").strip()
    # Try direct parse
    try:
        return json.loads(cleaned)
    except Exception:
        pass

    # Extract first JSON object
    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in LLM output.")
    return json.loads(match.group(0))