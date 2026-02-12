from typing import Optional

from config.prompts import RAG_SYSTEM_PROMPT
from config.settings import settings
from src.models.schemas import RAGResult
from src.services.llm_service import llm_service
from src.services.vector_store import vector_store
from src.utils.logger import get_logger

logger = get_logger(__name__)

NO_INFO_MESSAGE = "I don't have that information in my knowledge base."

_RAG_FOLLOW_UP_PREFIX = """[Follow-up question. Previous assistant answer: {previous_answer}]
User asks: {question}
Answer in the context of the previous answer if the user is asking for clarification or more detail."""


def _is_follow_up(question: str) -> bool:
    q = question.lower().strip()
    if len(q.split()) <= 5 and any(w in q for w in ("this", "that", "it", "mean", "explain", "what", "how")):
        return True
    return "what do you mean" in q or "explain" in q or "can you clarify" in q


class RAGTool:

    def __init__(self, top_k: Optional[int] = None) -> None:
        self.top_k = top_k if top_k is not None else settings.rag_top_k

    def query(
        self,
        question: str,
        top_k: Optional[int] = None,
        previous_assistant_message: Optional[str] = None,
    ) -> RAGResult:
        k = top_k if top_k is not None else self.top_k
        search_query = question
        if previous_assistant_message and _is_follow_up(question):
            search_query = f"{previous_assistant_message[:300]} {question}"
        docs = vector_store.similarity_search(search_query, top_k=k)

        if not docs:
            return RAGResult(
                answer=NO_INFO_MESSAGE,
                sources=[],
                confidence=0.0,
            )

        context = "\n\n".join(d["content"] for d in docs)
        sources = [d["content"] for d in docs]
        if previous_assistant_message and _is_follow_up(question):
            question = _RAG_FOLLOW_UP_PREFIX.format(
                previous_answer=previous_assistant_message[:500],
                question=question,
            )
        prompt = RAG_SYSTEM_PROMPT.format(context=context, question=question)
        answer = llm_service.generate(prompt).strip()

        if not answer or NO_INFO_MESSAGE.lower() in answer.lower():
            return RAGResult(
                answer=answer or NO_INFO_MESSAGE,
                sources=sources,
                confidence=0.0,
            )

        return RAGResult(answer=answer, sources=sources, confidence=1.0)


rag_tool = RAGTool()
