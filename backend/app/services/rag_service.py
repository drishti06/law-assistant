import os
import json
import pickle
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.config import get_settings
from app.utils.logger import logger

_model: SentenceTransformer | None = None
_index: faiss.IndexFlatL2 | None = None
_chunks: list[dict] = []


def _get_embedding_model() -> SentenceTransformer:
    global _model
    if _model is None:
        settings = get_settings()
        logger.info(f"Loading embedding model: {settings.embedding_model}")
        _model = SentenceTransformer(settings.embedding_model)
        logger.info("Embedding model loaded")
    return _model


def _get_index_paths() -> tuple[str, str]:
    settings = get_settings()
    index_path = settings.faiss_index_path
    return os.path.join(index_path, "index.faiss"), os.path.join(index_path, "chunks.pkl")


def chunk_documents(documents: list[dict]) -> list[dict]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = []
    for doc in documents:
        text_chunks = splitter.split_text(doc["content"])
        for i, chunk in enumerate(text_chunks):
            chunks.append({
                "text": chunk,
                "source": doc.get("title", "Unknown"),
                "category": doc.get("category", "general"),
                "chunk_index": i,
            })
    logger.info(f"Created {len(chunks)} chunks from {len(documents)} documents")
    return chunks


def build_index(chunks: list[dict]) -> faiss.IndexFlatL2:
    model = _get_embedding_model()
    texts = [c["text"] for c in chunks]
    embeddings = model.encode(texts, show_progress_bar=True, normalize_embeddings=True)
    embeddings = np.array(embeddings, dtype="float32")

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    logger.info(f"FAISS index built with {index.ntotal} vectors (dim={dimension})")
    return index


def save_index(index: faiss.IndexFlatL2, chunks: list[dict]):
    settings = get_settings()
    os.makedirs(settings.faiss_index_path, exist_ok=True)
    index_file, chunks_file = _get_index_paths()

    faiss.write_index(index, index_file)
    with open(chunks_file, "wb") as f:
        pickle.dump(chunks, f)
    logger.info(f"Index saved to {settings.faiss_index_path}")


def load_index() -> bool:
    global _index, _chunks
    index_file, chunks_file = _get_index_paths()

    if not os.path.exists(index_file) or not os.path.exists(chunks_file):
        logger.warning("No existing FAISS index found")
        return False

    _index = faiss.read_index(index_file)
    with open(chunks_file, "rb") as f:
        _chunks = pickle.load(f)

    logger.info(f"Loaded FAISS index with {_index.ntotal} vectors and {len(_chunks)} chunks")
    return True


def _extract_pdf_text(filepath: str) -> str:
    """Extract text from a PDF file using PyMuPDF."""
    import fitz  # PyMuPDF

    text_parts = []
    try:
        doc = fitz.open(filepath)
        for page_num, page in enumerate(doc):
            page_text = page.get_text("text")
            if page_text.strip():
                text_parts.append(page_text)
        doc.close()
        logger.info(f"Extracted text from PDF: {filepath} ({len(text_parts)} pages)")
    except Exception as e:
        logger.error(f"Failed to extract PDF {filepath}: {e}")

    return "\n\n".join(text_parts)


def load_documents_from_directory(directory: str = "data/legal_documents") -> list[dict]:
    documents = []
    if not os.path.exists(directory):
        logger.warning(f"Directory {directory} not found")
        return documents

    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)

        if filename.endswith(".txt"):
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            documents.append({
                "title": filename.replace(".txt", "").replace("_", " ").title(),
                "content": content,
                "category": "indian_law",
            })

        elif filename.endswith(".pdf"):
            content = _extract_pdf_text(filepath)
            if content.strip():
                documents.append({
                    "title": filename.replace(".pdf", "").replace("_", " ").title(),
                    "content": content,
                    "category": "indian_law",
                })

        elif filename.endswith(".json"):
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                documents.extend(data)
            else:
                documents.append(data)

    logger.info(f"Loaded {len(documents)} documents from {directory}")
    return documents


def add_pdf_document(filepath: str, title: str | None = None, category: str = "indian_law"):
    """Add a PDF file to the vector index."""
    content = _extract_pdf_text(filepath)
    if not content.strip():
        logger.warning(f"No text extracted from PDF: {filepath}")
        return 0

    doc_title = title or os.path.basename(filepath).replace(".pdf", "").replace("_", " ").title()
    add_document(doc_title, content, category)
    return len(content)


def initialize_rag():
    global _index, _chunks
    if load_index():
        return

    documents = load_documents_from_directory()
    if not documents:
        logger.warning("No legal documents found. RAG will not be available until documents are added.")
        return

    _chunks = chunk_documents(documents)
    _index = build_index(_chunks)
    save_index(_index, _chunks)


def add_document(title: str, content: str, category: str = "general"):
    global _index, _chunks
    new_chunks = chunk_documents([{"title": title, "content": content, "category": category}])

    model = _get_embedding_model()
    texts = [c["text"] for c in new_chunks]
    embeddings = model.encode(texts, normalize_embeddings=True)
    embeddings = np.array(embeddings, dtype="float32")

    if _index is None:
        dimension = embeddings.shape[1]
        _index = faiss.IndexFlatL2(dimension)
        _chunks = []

    _index.add(embeddings)
    _chunks.extend(new_chunks)
    save_index(_index, _chunks)
    logger.info(f"Added document '{title}' with {len(new_chunks)} chunks")


def retrieve(query: str, top_k: int = 5) -> list[dict]:
    if _index is None or not _chunks:
        logger.warning("FAISS index not initialized. Returning empty results.")
        return []

    model = _get_embedding_model()
    query_embedding = model.encode([query], normalize_embeddings=True)
    query_embedding = np.array(query_embedding, dtype="float32")

    distances, indices = _index.search(query_embedding, min(top_k, len(_chunks)))

    results = []
    for i, idx in enumerate(indices[0]):
        if idx < len(_chunks) and idx >= 0:
            results.append({
                **_chunks[idx],
                "score": float(distances[0][i]),
            })

    logger.debug(f"Retrieved {len(results)} chunks for query: {query[:80]}...")
    return results
