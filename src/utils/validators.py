import re
from typing import Optional

def normalize_city(name: Optional[str]) -> Optional[str]:
    if not name or not isinstance(name, str):
        return None
    return name.strip().title() or None

def parse_json_from_text(text: str) -> Optional[str]:
    if not text:
        return None
    match = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", text, re.DOTALL)
    if match:
        return match.group(0)
    start = text.find("{")
    if start != -1:
        end = text.rfind("}") + 1
        if end > start:
            return text[start:end]
    return None
