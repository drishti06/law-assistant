# AI Model Architecture & Working

This document explains how the core AI model pipeline works in the Legal Chatbot project -- focusing on the RAG (Retrieval-Augmented Generation) system, embedding models, vector search, and response generation.

---

## High-Level Overview

The chatbot uses a **RAG (Retrieval-Augmented Generation)** architecture. Instead of relying solely on a language model's training data, it retrieves relevant legal text from a vector database and feeds it as context to the model. This ensures responses are grounded in actual Indian law documents.

```
User Query
    |
    v
[1. Embedding Model] -- converts query to a vector
    |
    v
[2. FAISS Vector Search] -- finds most similar legal document chunks
    |
    v
[3. Context Assembly] -- top matching chunks are combined
    |
    v
[4. LLM / Text Generation] -- generates a structured legal answer using the context
    |
    v
Structured Response (Short Answer, Explanation, Relevant Law, Next Steps, Disclaimer)
```

---

## Step 1: Document Ingestion & Chunking

Before the chatbot can answer questions, legal documents must be processed and indexed.

### Source Documents
The system loads legal documents from `data/legal_documents/` (`.txt`, `.pdf`, `.json` formats). These cover Indian law topics like IPC, CrPC, Fundamental Rights, Consumer Protection, Cyber Law, Family Law, and Labour Law.

### Text Chunking
Documents are split into small, overlapping chunks using `RecursiveCharacterTextSplitter` from LangChain:

- **Chunk size**: 500 characters
- **Chunk overlap**: 50 characters
- **Separators**: `\n\n`, `\n`, `. `, ` `, `""`

This ensures each chunk is small enough to be meaningfully embedded while preserving context across chunk boundaries. Each chunk retains metadata (source document name, category, chunk index).

---

## Step 2: Embedding Generation

Each text chunk is converted into a dense numerical vector (embedding) using the **Sentence Transformers** library.

### Embedding Model: `all-MiniLM-L6-v2`

- **Type**: Pre-trained sentence transformer from HuggingFace
- **Output dimension**: 384-dimensional vectors
- **What it does**: Maps text into a vector space where semantically similar texts are close together
- **Why this model**: It is lightweight, fast, and produces high-quality embeddings for semantic similarity tasks -- ideal for retrieval on modest hardware

Embeddings are **L2-normalized** before indexing, which makes the L2 distance equivalent to cosine distance for similarity search.

---

## Step 3: FAISS Vector Index

The embeddings are stored in a **FAISS (Facebook AI Similarity Search)** index.

### Index Type: `IndexFlatL2`

- **Algorithm**: Exact L2 (Euclidean) distance search
- **How it works**: When a query comes in, its embedding is compared against every stored vector using L2 distance. The closest vectors correspond to the most semantically relevant document chunks.
- **Trade-off**: Flat index gives exact results (no approximation) -- suitable for the moderate dataset size of legal documents

### Index Persistence
- The FAISS index is saved to disk (`data/faiss_index/index.faiss`) along with chunk metadata (`chunks.pkl`)
- On first startup, documents are loaded, chunked, embedded, and indexed (takes 1-2 minutes)
- On subsequent startups, the cached index is loaded directly

---

## Step 4: Retrieval (Semantic Search)

When a user sends a query:

1. The query text is embedded using the same `all-MiniLM-L6-v2` model
2. FAISS searches for the **top-k nearest vectors** (default k=5)
3. The corresponding text chunks are returned with their distance scores
4. These chunks form the **context** for response generation

This is the "Retrieval" part of RAG -- the model doesn't guess from general knowledge; it retrieves actual legal text that matches the user's question.

---

## Step 5: Response Generation (Two Modes)

### Mode A: HuggingFace Model (Default -- No API Key Needed)

**Model**: `google/flan-t5-base`

- **Type**: Text-to-text generation model (encoder-decoder transformer)
- **Parameters**: ~250M
- **How it's used**: The retrieved context chunks and the user query are combined into a prompt. The model generates a summarized answer.
- **Generation settings**: `max_new_tokens=512`, `temperature=0.3`, `do_sample=True`
- **Fallback logic**: If the model output is too short (<30 chars), contains template placeholders, or fails entirely, the system falls back to directly assembling the answer from the retrieved context chunks

### Mode B: OpenAI GPT-3.5 (Optional -- Requires API Key)

When `USE_OPENAI=true` and an API key is configured:

- **Model**: `gpt-3.5-turbo`
- **How it's used**: The retrieved context is sent as part of a chat completion request with a system prompt instructing the model to act as an Indian law specialist
- **Generation settings**: `temperature=0.7`, `max_tokens=1024`
- **Advantage**: Produces more fluent, detailed, and well-structured responses compared to the local model

---

## Step 6: Response Structuring

Regardless of the generation mode, every response is parsed/assembled into a structured format:

| Field | Description |
|-------|-------------|
| **Short Answer** | 1-2 sentence direct answer |
| **Explanation** | Detailed answer grounded in retrieved legal text |
| **Relevant Law/Section** | Specific sections, articles, and acts extracted via regex patterns (e.g., "Section 498A IPC", "Article 21") |
| **Next Steps** | Practical advice based on query category (FIR filing, bail, divorce, consumer complaint, etc.) |
| **Disclaimer** | Legal disclaimer (available in English and Hindi) |

### Law Reference Extraction
The system uses regex patterns to automatically extract legal citations from the context:
- `Section X of [Act]`
- `Article X of the Constitution`
- Named codes like `IPC`, `CrPC`, `IT Act`, `BNS`, `BNSS`

### Next Steps Logic
Keyword-based matching on the query determines which category of practical advice to provide (e.g., queries about "FIR" or "police" get steps for filing a police report; queries about "bail" get steps for the bail process).

---

## Dynamic Document Addition

New legal documents can be added at runtime via the admin API:
1. The new document is chunked using the same splitter
2. Chunks are embedded using the same model
3. New vectors are appended to the existing FAISS index
4. The updated index is saved to disk

This allows the knowledge base to grow without rebuilding the entire index.

---

## Model Summary Table

| Component | Model / Tool | Purpose |
|-----------|-------------|---------|
| Embedding | `all-MiniLM-L6-v2` (Sentence Transformers) | Convert text to 384-dim vectors for semantic search |
| Vector Store | FAISS `IndexFlatL2` | Store and search embeddings by similarity |
| Text Generation (default) | `google/flan-t5-base` (HuggingFace) | Generate answers from context locally |
| Text Generation (optional) | `gpt-3.5-turbo` (OpenAI) | Generate higher-quality answers via API |
| Text Splitter | `RecursiveCharacterTextSplitter` (LangChain) | Split documents into embeddable chunks |

---

## Why RAG Over Fine-Tuning?

- **No training required** -- legal documents are indexed as-is, no GPU-intensive fine-tuning
- **Easy to update** -- new laws or amendments can be added by simply uploading documents
- **Grounded answers** -- responses cite actual legal text rather than hallucinated information
- **Transparent** -- the retrieved sources are traceable, making it possible to verify answers
- **Cost-effective** -- runs locally with the HuggingFace model; OpenAI is optional for better quality
