from typing import Iterator, List

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class LLMService:

    def __init__(self) -> None:
        self.chat_model = ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.google_api_key,
            temperature=settings.temperature,
            max_output_tokens=settings.max_tokens,
        )
        self.embedding_model = GoogleGenerativeAIEmbeddings(
            model=settings.gemini_embedding_model,
            google_api_key=settings.google_api_key,
        )
        logger.info("Initialized LLM service with model: %s", settings.gemini_model)

    def generate(self, prompt: str, **kwargs: object) -> str:
        try:
            response = self.chat_model.invoke(prompt, **kwargs)
            return response.content if hasattr(response, "content") else str(response)
        except Exception as e:
            logger.error("LLM generation error: %s", e)
            raise

    def generate_stream(self, prompt: str, **kwargs: object) -> Iterator[str]:
        try:
            for chunk in self.chat_model.stream(prompt, **kwargs):
                if hasattr(chunk, "content") and chunk.content:
                    yield chunk.content
        except Exception as e:
            logger.error("LLM streaming error: %s", e)
            raise

    def embed_text(self, text: str) -> List[float]:
        try:
            return self.embedding_model.embed_query(text)
        except Exception as e:
            logger.error("Embedding error: %s", e)
            raise

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        try:
            return self.embedding_model.embed_documents(texts)
        except Exception as e:
            logger.error("Batch embedding error: %s", e)
            raise



llm_service = LLMService()
