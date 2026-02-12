from typing import Any, Dict, List

def format_flight_summary(flight: Any) -> str:
    parts = [
        f"{getattr(flight, 'airline', 'Unknown')}",
        f"{getattr(flight, 'origin', '')} → {getattr(flight, 'destination', '')}",
        f"Dep: {getattr(flight, 'departure_date', '')}",
        f"${getattr(flight, 'price_usd', 0):.0f}",
    ]
    return " | ".join(parts)


def format_criteria_summary(criteria: Dict[str, Any]) -> str:
    parts = []
    for k, v in criteria.items():
        if v is None or v == "" or v == []:
            continue
        if isinstance(v, bool) and not v:
            continue
        parts.append(f"{k}: {v}")
    return ", ".join(parts) if parts else "No criteria"
