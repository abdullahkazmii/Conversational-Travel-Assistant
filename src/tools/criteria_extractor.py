import json
import re

from config.prompts import CRITERIA_EXTRACTION_PROMPT
from src.models.enums import Alliance, TripType
from src.models.schemas import FlightCriteria
from src.services.llm_service import llm_service
from src.utils.logger import get_logger
from src.utils.validators import parse_json_from_text

logger = get_logger(__name__)


def extract_criteria(query: str, conversation_context: str = "") -> FlightCriteria:
    prompt = CRITERIA_EXTRACTION_PROMPT.format(
        query=query,
        conversation_context=conversation_context,
    )
    response = llm_service.generate(prompt).strip()

    json_str = response
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", response)
    if match:
        json_str = match.group(1).strip()
    else:
        extracted = parse_json_from_text(response)
        if extracted:
            json_str = extracted

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.warning("Criteria JSON parse failed: %s", e)
        raise ValueError(f"Could not parse criteria from response: {e}") from e

    if data.get("trip_type"):
        try:
            data["trip_type"] = TripType(data["trip_type"])
        except (ValueError, TypeError):
            data["trip_type"] = TripType.ROUND_TRIP
    if data.get("alliance"):
        try:
            data["alliance"] = Alliance(data["alliance"]) if data["alliance"] else None
        except (ValueError, TypeError):
            data["alliance"] = None

    if "destination" in data and (data["destination"] is None or data["destination"] == "null"):
        data["destination"] = None
    if "origin" in data and (data["origin"] is None or data["origin"] == "null"):
        data["origin"] = None

    # Ensure required string fields are never None (LLM often returns null)
    if data.get("departure_date") is None or data.get("departure_date") == "null":
        data["departure_date"] = "flexible"
    if data.get("return_date") is None or data.get("return_date") == "null":
        data["return_date"] = None  # keep as None for one-way

    return FlightCriteria.model_validate(data)
