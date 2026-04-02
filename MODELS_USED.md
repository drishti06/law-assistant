# AI/ML Models Used in This Project

## 1. LLM (Text Generation) — Answer Generation

| Model | Source | Status | Purpose |
|-------|--------|--------|---------|
| **google/flan-t5-base** | HuggingFace (local) | **Active (default)** | Generates summarized legal answers from retrieved context |
| **gpt-3.5-turbo** | OpenAI API | **Off** (`USE_OPENAI=false`) | Higher quality answers — enable via `.env` |

### Configuration
- `HF_MODEL_NAME=google/flan-t5-base` — local model (free, ~250M params)
- `USE_OPENAI=false` — set to `true` + add `OPENAI_API_KEY` to use GPT-3.5
- Flan-T5 settings: `max_new_tokens=512`, `temperature=0.3`
- GPT-3.5 settings: `max_tokens=512`, `temperature=0.7`

---

## 2. Embedding Model — Semantic Search

| Model | Source | Output | Purpose |
|-------|--------|--------|---------|
| **all-MiniLM-L6-v2** | Sentence Transformers (HuggingFace) | 384-dim vectors | Converts documents & queries into vectors for similarity search |

### Configuration
- `EMBEDDING_MODEL=all-MiniLM-L6-v2`
- L2-normalized embeddings
- Used for both document indexing and query encoding

---

## 3. Vector Database — Similarity Search

| Tool | Type | Purpose |
|------|------|---------|
| **FAISS (IndexFlatL2)** | Facebook AI Similarity Search | Stores embeddings and finds top-5 similar document chunks |

### Configuration
- `FAISS_INDEX_PATH=data/faiss_index`
- Index type: `IndexFlatL2` (exact L2/Euclidean distance)
- Default `top_k=5`, `max_distance=1.5`
- Stored in: `backend/data/faiss_index/`

---

## 4. Text Processing Tools

| Tool | Library | Purpose |
|------|---------|---------|
| **RecursiveCharacterTextSplitter** | LangChain | Splits legal documents into 1000-char chunks (200 overlap) |
| **PyMuPDF (fitz)** | PyMuPDF | Extracts text from PDF legal documents |

---

## 5. RAG Pipeline Flow

```
User Query
    |
    v
all-MiniLM-L6-v2 (embed query into 384-dim vector)
    |
    v
FAISS IndexFlatL2 (search top-5 similar document chunks)
    |
    v
flan-t5-base / gpt-3.5-turbo (generate answer from context)
    |
    v
Structured Response (What This Means, Your Rights, What To Do, Get Help)
```

---

## 6. Key Dependencies

| Library | Version | Purpose |
|---------|---------|---------|
| `sentence-transformers` | 3.0.1 | Embedding model loading |
| `faiss-cpu` | 1.8.0 | Vector similarity search |
| `openai` | 1.35.3 | OpenAI API client (optional) |
| `langchain-text-splitters` | 0.2.2 | Document chunking |
| `numpy` | 1.26.4 | Numerical operations |
| `PyMuPDF` | 1.24.5 | PDF text extraction |

---

## 7. Key Files

| File | Contains |
|------|----------|
| `backend/app/services/llm_service.py` | LLM integration (flan-t5 + OpenAI) |
| `backend/app/services/rag_service.py` | Embedding model + FAISS index + retrieval |
| `backend/app/config.py` | Model configuration & settings |
| `backend/.env` | Environment variables (model names, API keys) |
| `backend/requirements.txt` | All ML/AI dependencies |

---

**Total AI Models: 3** — google/flan-t5-base, gpt-3.5-turbo (optional), all-MiniLM-L6-v2
