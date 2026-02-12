from langgraph.graph import END, StateGraph

from src.agents.nodes import (
    clarification_node,
    criteria_extraction_node,
    flight_search_node,
    rag_query_node,
    response_generation_node,
    router_node,
)
from src.agents.state import TravelAssistantState
from src.models.enums import IntentType, NodeName
from src.utils.logger import get_logger

logger = get_logger(__name__)


def create_travel_assistant_graph() -> StateGraph:
    workflow = StateGraph(TravelAssistantState)

    workflow.add_node(NodeName.ROUTER.value, router_node)
    workflow.add_node(NodeName.CRITERIA_EXTRACTION.value, criteria_extraction_node)
    workflow.add_node(NodeName.FLIGHT_SEARCH.value, flight_search_node)
    workflow.add_node(NodeName.RAG_QUERY.value, rag_query_node)
    workflow.add_node(NodeName.RESPONSE_GENERATION.value, response_generation_node)
    workflow.add_node(NodeName.CLARIFICATION.value, clarification_node)

    workflow.set_entry_point(NodeName.ROUTER.value)

    def route_based_on_intent(state: TravelAssistantState) -> str:
        intent = state.get("intent")
        if intent == IntentType.FLIGHT_SEARCH:
            return NodeName.CRITERIA_EXTRACTION.value
        if intent in (
            IntentType.VISA_QUERY,
            IntentType.POLICY_QUERY,
            IntentType.GENERAL_TRAVEL,
        ):
            return NodeName.RAG_QUERY.value
        return NodeName.CLARIFICATION.value

    workflow.add_conditional_edges(
        NodeName.ROUTER.value,
        route_based_on_intent,
    )

    def check_clarification_needed(state: TravelAssistantState) -> str:
        if state.get("needs_clarification"):
            return NodeName.CLARIFICATION.value
        return NodeName.FLIGHT_SEARCH.value

    workflow.add_conditional_edges(
        NodeName.CRITERIA_EXTRACTION.value,
        check_clarification_needed,
    )

    workflow.add_edge(NodeName.FLIGHT_SEARCH.value, NodeName.RESPONSE_GENERATION.value)
    workflow.add_edge(NodeName.RAG_QUERY.value, END)
    workflow.add_edge(NodeName.RESPONSE_GENERATION.value, END)
    workflow.add_edge(NodeName.CLARIFICATION.value, END)

    compiled = workflow.compile()
    logger.info("Travel assistant graph compiled successfully")
    return compiled

travel_assistant_graph = create_travel_assistant_graph()
