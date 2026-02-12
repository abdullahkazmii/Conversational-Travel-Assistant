from enum import Enum


class IntentType(str, Enum):
    """User intent categories."""

    FLIGHT_SEARCH = "FLIGHT_SEARCH"
    VISA_QUERY = "VISA_QUERY"
    POLICY_QUERY = "POLICY_QUERY"
    GENERAL_TRAVEL = "GENERAL_TRAVEL"
    CLARIFICATION_NEEDED = "CLARIFICATION_NEEDED"


class TripType(str, Enum):
    """Flight trip types."""

    ONE_WAY = "one-way"
    ROUND_TRIP = "round-trip"
    MULTI_CITY = "multi-city"


class Alliance(str, Enum):
    """Airline alliances."""

    STAR_ALLIANCE = "Star Alliance"
    ONEWORLD = "Oneworld"
    SKYTEAM = "SkyTeam"


class NodeName(str, Enum):
    """LangGraph node identifiers."""

    ROUTER = "router"
    CRITERIA_EXTRACTION = "criteria_extraction"
    FLIGHT_SEARCH = "flight_search"
    RAG_QUERY = "rag_query"
    RESPONSE_GENERATION = "response_generation"
    CLARIFICATION = "clarification"
    END = "end"
