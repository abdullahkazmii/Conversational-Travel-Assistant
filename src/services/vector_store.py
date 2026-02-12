from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from config.settings import settings
from src.services.llm_service import llm_service
from src.utils.logger import get_logger

logger = get_logger(__name__)


class VectorStoreService:
    def __init__(self) -> None:
        persist_dir = Path(settings.chroma_persist_directory)
        persist_dir.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=str(persist_dir),
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )

        try:
            self.collection = self.client.get_collection(
                name=settings.chroma_collection_name
            )
            logger.info("Loaded existing collection: %s", settings.chroma_collection_name)
        except Exception as e:
            logger.debug("Collection not found, creating: %s", e)
            self.collection = self.client.create_collection(
                name=settings.chroma_collection_name,
                metadata={"description": "Travel knowledge base"},
            )
            logger.info("Created new collection: %s", settings.chroma_collection_name)

    def add_documents(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> None:
        """
        Add documents to the vector store.
        """
        try:
            embeddings = llm_service.embed_documents(texts)
            if ids is None:
                ids = [f"doc_{i}" for i in range(len(texts))]
            self.collection.add(
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas or [{}] * len(texts),
                ids=ids,
            )
            logger.info("Added %d documents to vector store", len(texts))
        except Exception as e:
            logger.error("Error adding documents: %s", e)
            raise

    def similarity_search(
        self,
        query: str,
        top_k: int = 3,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        try:
            query_embedding = llm_service.embed_text(query)
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filter_metadata,
            )
            documents: List[Dict[str, Any]] = []
            docs = results.get("documents", [[]])
            metas = results.get("metadatas", [[]])
            dists = results.get("distances", [[]])
            if docs and docs[0]:
                for i in range(len(docs[0])):
                    doc = {
                        "content": docs[0][i],
                        "metadata": metas[0][i] if metas and metas[0] else {},
                    }
                    if dists and dists[0] and i < len(dists[0]):
                        doc["distance"] = dists[0][i]
                    documents.append(doc)
            logger.info("Found %d similar documents for query", len(documents))
            return documents
        except Exception as e:
            logger.error("Error searching vector store: %s", e)
            raise

    def reset(self) -> None:
        self.client.delete_collection(settings.chroma_collection_name)
        self.collection = self.client.create_collection(
            name=settings.chroma_collection_name,
            metadata={"description": "Travel knowledge base"},
        )
        logger.info("Reset vector store")

vector_store = VectorStoreService()
