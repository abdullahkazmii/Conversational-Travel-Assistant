import json
from typing import Any, Dict, List

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from config.prompts import (
    CLARIFICATION_PROMPT,
    FLIGHT_RESULTS_FORMAT_PROMPT,
    INTENT_CLASSIFICATION_PROMPT,
    NO_RESULTS_PROMPT,
)
from src.agents.state import TravelAssistantState
from src.models.enums import IntentType
from src.services.llm_service import llm_service
from src.tools.criteria_extractor import extract_criteria
from src.tools.flight_search import flight_search_tool
from src.tools.rag_retrieval import rag_tool
from src.utils.logger import get_logger

logger = get_logger(__name__)

CONVERSATION_CONTEXT_MESSAGES = 6


def _format_recent_messages(messages: List[BaseMessage], last_n: int = CONVERSATION_CONTEXT_MESSAGES) -> str:
    if not messages:
        return ""
    recent = messages[-last_n:] if len(messages) > last_n else messages
    lines = []
    for msg in recent:
        role = "User" if isinstance(msg, HumanMessage) else "Assistant"
        content = getattr(msg, "content", str(msg))
        if content:
            lines.append(f"{role}: {content}")
    return "\n".join(lines)


def router_node(state: TravelAssistantState) -> Dict[str, Any]:
    logger.info("Executing router_node")
    try:
        query = state["user_query"]
        messages = state.get("messages") or []
        if len(messages) > 1:
            context = _format_recent_messages(messages[:-1])
            conversation_context = f"Recent conversation:\n{context}\n\n" if context else ""
        else:
            conversation_context = ""
        prompt = INTENT_CLASSIFICATION_PROMPT.format(
            query=query,
            conversation_context=conversation_context,
        )
        response = llm_service.generate(prompt).strip()
        intent = IntentType.CLARIFICATION_NEEDED
        for intent_type in IntentType:
            if intent_type.value in response:
                intent = intent_type
                break
        logger.info("Classified intent: %s", intent.value)
        return {**state, "intent": intent}
    except Exception as e:
        logger.error("Error in router_node: %s", e)
        return {
            **state,
            "intent": IntentType.CLARIFICATION_NEEDED,
            "error": str(e),
        }


def criteria_extraction_node(state: TravelAssistantState) -> Dict[str, Any]:
    logger.info("Executing criteria_extraction_node")
    try:
        query = state["user_query"]
        messages = state.get("messages") or []
        if len(messages) > 1:
            context = _format_recent_messages(messages)
            conversation_context = f"Conversation:\n{context}\n\n"
        else:
            conversation_context = ""
        criteria = extract_criteria(query, conversation_context=conversation_context)
        needs_clarification = not (criteria.destination and criteria.destination.strip())
        logger.info("Extracted criteria: %s", criteria.model_dump())
        return {
            **state,
            "extracted_criteria": criteria,
            "needs_clarification": needs_clarification,
        }
    except Exception as e:
        logger.error("Error in criteria_extraction_node: %s", e)
        return {
            **state,
            "needs_clarification": True,
            "error": str(e),
        }


def flight_search_node(state: TravelAssistantState) -> Dict[str, Any]:
    logger.info("Executing flight_search_node")
    try:
        criteria = state.get("extracted_criteria")
        if not criteria:
            return {**state, "search_results": [], "error": "No criteria extracted"}
        results = flight_search_tool.search(criteria)
        logger.info("Found %d flights", len(results))
        return {**state, "search_results": results}
    except Exception as e:
        logger.error("Error in flight_search_node: %s", e)
        return {**state, "search_results": [], "error": str(e)}


def rag_query_node(state: TravelAssistantState) -> Dict[str, Any]:
    logger.info("Executing rag_query_node")
    try:
        query = state["user_query"]
        messages = state.get("messages") or []
        previous_response = ""
        for msg in reversed(messages):
            if isinstance(msg, AIMessage):
                previous_response = getattr(msg, "content", "") or ""
                break
        result = rag_tool.query(query, previous_assistant_message=previous_response or None)
        logger.info("RAG answer generated with %d sources", len(result.sources))
        return {
            **state,
            "final_response": result.answer,
            "rag_context": "\n".join(result.sources),
        }
    except Exception as e:
        logger.error("Error in rag_query_node: %s", e)
        return {
            **state,
            "final_response": "I'm sorry, I encountered an error retrieving that information.",
            "error": str(e),
        }


def response_generation_node(state: TravelAssistantState) -> Dict[str, Any]:
    logger.info("Executing response_generation_node")
    if state.get("final_response"):
        return dict(state)
    try:
        results = state.get("search_results") or []
        criteria = state.get("extracted_criteria")
        criteria_dict = criteria.model_dump() if criteria else {}
        if not results:
            prompt = NO_RESULTS_PROMPT.format(criteria=json.dumps(criteria_dict, indent=2))
        else:
            results_text = json.dumps(
                [r.model_dump(mode="json") for r in results[:5]],
                indent=2,
            )
            prompt = FLIGHT_RESULTS_FORMAT_PROMPT.format(
                criteria=json.dumps(criteria_dict, indent=2),
                results=results_text,
                count=len(results),
            )
        response = llm_service.generate(prompt)
        return {**state, "final_response": response}
    except Exception as e:
        logger.error("Error in response_generation_node: %s", e)
        return {
            **state,
            "final_response": "I apologize, but I encountered an error generating the response.",
            "error": str(e),
        }


def clarification_node(state: TravelAssistantState) -> Dict[str, Any]:
    logger.info("Executing clarification_node")
    try:
        query = state["user_query"]
        messages = state.get("messages") or []
        conversation_context = _format_recent_messages(messages) if messages else ""
        criteria = state.get("extracted_criteria")
        missing_fields = []
        if criteria:
            if not (criteria.destination and criteria.destination.strip()):
                missing_fields.append("destination city")
            if not (criteria.origin and criteria.origin.strip()) and not missing_fields:
                missing_fields.append("origin city or dates")
        if not missing_fields:
            missing_fields.append("travel details")
        prompt = CLARIFICATION_PROMPT.format(
            query=query,
            missing_fields=", ".join(missing_fields),
            conversation_context=conversation_context or "(none yet)",
        )
        response = llm_service.generate(prompt)
        return {**state, "final_response": response}
    except Exception as e:
        logger.error("Error in clarification_node: %s", e)
        return {
            **state,
            "final_response": "Could you provide more details about your travel plans?",
            "error": str(e),
        }
