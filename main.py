import sys
from typing import List

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from src.agents.graph import travel_assistant_graph
from src.agents.state import TravelAssistantState
from src.utils.logger import get_logger

logger = get_logger(__name__)


def run() -> None:
    messages: List[BaseMessage] = []
    sys.stdout.write("Travel Assistant. Type your message and press Enter (Ctrl+D or 'exit' to quit).\n\n")
    sys.stdout.flush()

    while True:
        try:
            user_input = input("You: ").strip()
        except EOFError:
            break
        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit", "q"):
            break

        messages.append(HumanMessage(content=user_input))
        state: TravelAssistantState = {
            "messages": messages,
            "user_query": user_input,
            "intent": None,
            "extracted_criteria": None,
            "search_results": None,
            "rag_context": None,
            "final_response": None,
            "needs_clarification": False,
            "error": None,
        }

        try:
            result = travel_assistant_graph.invoke(state)
            response = result.get("final_response") or "I couldn't process your request."
            sys.stdout.write(f"Assistant: {response}\n")
            sys.stdout.flush()
            messages.append(AIMessage(content=response))
        except Exception as e:
            logger.exception("Error processing request: %s", e)
            fallback = "I'm sorry, something went wrong. Please try again."
            sys.stdout.write(f"Assistant: {fallback}\n")
            sys.stdout.flush()
            messages.append(AIMessage(content=fallback))


if __name__ == "__main__":
    run()
