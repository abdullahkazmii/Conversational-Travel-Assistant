from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from src.models.enums import Alliance, TripType


class FlightCriteria(BaseModel):
    """Structured flight search criteria."""

    origin: Optional[str] = Field(None, description="Departure city")
    destination: Optional[str] = Field(None, description="Arrival city")
    departure_date: str = Field("flexible", description="Departure date or range")
    return_date: Optional[str] = Field(None, description="Return date")
    trip_type: TripType = Field(TripType.ROUND_TRIP, description="Trip type")
    alliance: Optional[Alliance] = Field(None, description="Preferred alliance")
    preferred_airlines: Optional[List[str]] = Field(None, description="Preferred airlines")
    avoid_overnight_layover: bool = Field(False, description="Avoid overnight layovers")
    max_layovers: Optional[int] = Field(None, description="Maximum layover count")
    max_price_usd: Optional[float] = Field(None, description="Maximum price")
    refundable_only: bool = Field(False, description="Only refundable tickets")
    flexible_dates: bool = Field(False, description="Flexible with dates")


class Flight(BaseModel):
    """Flight listing model."""

    airline: str
    alliance: Optional[str] = None
    origin: str = Field(..., alias="from")
    destination: str = Field(..., alias="to")
    departure_date: str
    return_date: Optional[str] = None
    layovers: List[str] = Field(default_factory=list)
    price_usd: float
    refundable: bool = False
    overnight_layover: bool = False
    match_score: float = Field(0.0, description="Calculated relevance score")

    model_config = ConfigDict(populate_by_name=True)


class RAGQuery(BaseModel):
    """RAG retrieval query."""

    question: str = Field(..., description="User's question")
    top_k: int = Field(3, description="Number of chunks to retrieve")
    previous_context: Optional[str] = Field(None, description="Previous conversation context")


class RAGResult(BaseModel):
    """RAG retrieval result."""

    answer: str = Field(..., description="Generated answer")
    sources: List[str] = Field(default_factory=list, description="Source documents")
    confidence: float = Field(1.0, description="Answer confidence score")


class ConversationMessage(BaseModel):
    """Chat message model."""

    role: str = Field(..., description="user or assistant")
    content: str = Field(..., description="Message content")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
