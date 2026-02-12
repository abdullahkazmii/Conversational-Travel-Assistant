import re
from pathlib import Path
from typing import List, Optional, Tuple

from config.settings import settings
from src.services.vector_store import vector_store
from src.utils.logger import get_logger

logger = get_logger(__name__)

DEFAULT_KB_DIR = Path("data/knowledge_base")
DEFAULT_VISA_RULES = Path("data/visa_rules.md")
CHUNK_SIZE = 600


def _chunk_text(text: str, max_chars: int = CHUNK_SIZE) -> List[str]:
    chunks: List[str] = []
    # Split by ## headers first to keep sections together when small enough
    sections = re.split(r"\n(?=##\s)", text.strip())
    for section in sections:
        section = section.strip()
        if not section:
            continue
        if len(section) <= max_chars:
            chunks.append(section)
            continue
        # Split long sections by paragraph
        paragraphs = re.split(r"\n\s*\n", section)
        current: List[str] = []
        current_len = 0
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            if current_len + len(para) + 2 <= max_chars:
                current.append(para)
                current_len += len(para) + 2
            else:
                if current:
                    chunks.append("\n\n".join(current))
                if len(para) > max_chars:
                    # Hard split
                    for i in range(0, len(para), max_chars):
                        chunks.append(para[i : i + max_chars])
                    current = []
                    current_len = 0
                else:
                    current = [para]
                    current_len = len(para) + 2
        if current:
            chunks.append("\n\n".join(current))
    return chunks


def load_and_chunk_file(path: Path, source_name: str) -> List[Tuple[str, dict]]:
    if not path.exists():
        logger.warning("File not found: %s", path)
        return []
    text = path.read_text(encoding="utf-8")
    chunk_texts = _chunk_text(text, max_chars=settings.rag_chunk_size)
    return [(c, {"source": source_name}) for c in chunk_texts]


def run(
    kb_dir: Optional[Path] = None,
    visa_rules_path: Optional[Path] = None,
    reset: bool = True,
) -> None:
    kb_dir = kb_dir or DEFAULT_KB_DIR
    visa_rules_path = visa_rules_path or DEFAULT_VISA_RULES

    all_chunks: List[str] = []
    all_metadatas: List[dict] = []
    all_ids: List[str] = []
    idx = 0

    if kb_dir.exists():
        for md_file in sorted(kb_dir.glob("*.md")):
            pairs = load_and_chunk_file(md_file, md_file.name)
            for text, meta in pairs:
                all_chunks.append(text)
                all_metadatas.append(meta)
                all_ids.append(f"{md_file.stem}_{idx}")
                idx += 1
    else:
        logger.warning("Knowledge base directory not found: %s", kb_dir)

    if visa_rules_path.exists():
        for text, meta in load_and_chunk_file(visa_rules_path, visa_rules_path.name):
            all_chunks.append(text)
            all_metadatas.append(meta)
            all_ids.append(f"visa_rules_{idx}")
            idx += 1

    if not all_chunks:
        logger.warning("No chunks loaded; check paths.")
        return

    if reset:
        vector_store.reset()

    vector_store.add_documents(
        texts=all_chunks,
        metadatas=all_metadatas,
        ids=all_ids,
    )
    logger.info("Knowledge base initialized with %d chunks", len(all_chunks))


if __name__ == "__main__":
    run()
