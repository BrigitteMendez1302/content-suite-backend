import json
import re
from typing import Any

def extract_json(text: str) -> Any:
    """
    Best-effort JSON extractor for LLM outputs.
    - Strips code fences
    - Grabs first {...} block
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