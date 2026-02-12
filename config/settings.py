from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # API Configuration
    google_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    gemini_embedding_model: str = "gemini-embedding-001"

    # ChromaDB Configuration
    chroma_persist_directory: str = "./data/vectorstore"
    chroma_collection_name: str = "travel_knowledge_base"

    # Application Settings
    log_level: str = "INFO"
    max_search_results: int = 5
    rag_top_k: int = 3
    rag_chunk_size: int = 600

    # Temperature settings
    temperature: float = 0.7
    max_tokens: int = 2048

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


# Global settings instance
settings = Settings()
