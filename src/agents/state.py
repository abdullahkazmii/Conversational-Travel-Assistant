from typing import List, Optional, TypedDict
from langchain_core.messages import BaseMessage
from src.models.enums import IntentType
from src.models.schemas import Flight, FlightCriteria

class TravelAssistantState(TypedDict, total=False):
    messages: List[BaseMessage]
    user_query: str
    intent: Optional[IntentType]
    extracted_criteria: Optional[FlightCriteria]
    search_results: Optional[List[Flight]]
    rag_context: Optional[str]
    final_response: Optional[str]
    needs_clarification: bool
    error: Optional[str]
