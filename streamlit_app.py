import streamlit as st

from langchain_core.messages import AIMessage, HumanMessage

from src.agents.graph import travel_assistant_graph
from src.agents.state import TravelAssistantState
from src.utils.logger import get_logger

logger = get_logger(__name__)

st.set_page_config(
    page_title="Travel Assistant",
    layout="centered",
)

if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("Conversational Travel Assistant")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask about flights, visas, or travel policies..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        try:
            state: TravelAssistantState = {
                "messages": [
                    HumanMessage(content=m["content"])
                    if m["role"] == "user"
                    else AIMessage(content=m["content"])
                    for m in st.session_state.messages
                ],
                "user_query": prompt,
                "intent": None,
                "extracted_criteria": None,
                "search_results": None,
                "rag_context": None,
                "final_response": None,
                "needs_clarification": False,
                "error": None,
            }
            with st.spinner("Thinking..."):
                result = travel_assistant_graph.invoke(state)
            response = result.get("final_response") or "I couldn't process your request."
            placeholder.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
        except Exception as e:
            logger.error("Chat error: %s", e)
            placeholder.markdown("I'm sorry, something went wrong. Please try again.")
            st.session_state.messages.append(
                {"role": "assistant", "content": "I'm sorry, something went wrong. Please try again."}
            )
