# Legal Chatbot for Indian Law

AI-powered legal assistant specializing in Indian law. Built with Next.js, FastAPI, FAISS, and MongoDB.

## Features

- **Chat Interface** - Clean ChatGPT-like UI with structured legal responses
- **RAG System** - Retrieval-Augmented Generation using FAISS + sentence-transformers
- **Structured Responses** - Short answer, explanation, relevant law/section, next steps, disclaimer
- **Multilingual** - English and Hindi support
- **Authentication** - JWT-based auth with cookie storage
- **Chat History** - Per-user chat history stored in MongoDB
- **Admin Panel** - Upload new legal documents into vector DB
- **Logging** - Debug logging to file and console

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14 (App Router), TypeScript, Tailwind CSS |
| Backend | FastAPI, Python 3.11+ |
| NLP | HuggingFace Transformers, sentence-transformers |
| Vector DB | FAISS |
| Database | MongoDB |
| Auth | JWT (httponly cookies) |
| Optional LLM | OpenAI GPT-3.5 |

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Settings management
│   │   ├── database.py          # MongoDB connection
│   │   ├── routes/
│   │   │   ├── auth.py          # POST /auth/login, /auth/register, /auth/logout
│   │   │   ├── chat.py          # POST /chat, GET /history
│   │   │   └── admin.py         # POST /admin/upload-document, GET /admin/stats
│   │   ├── services/
│   │   │   ├── rag_service.py   # FAISS indexing & retrieval
│   │   │   └── llm_service.py   # LLM response generation
│   │   ├── models/
│   │   │   ├── user.py          # User schemas
│   │   │   └── chat.py          # Chat schemas
│   │   └── utils/
│   │       ├── auth.py          # JWT + password hashing
│   │       └── logger.py        # Logging setup
│   ├── data/
│   │   └── legal_documents/     # Sample legal documents (IPC, CrPC, etc.)
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx             # Landing page
│   │   ├── chat/page.tsx        # Chat interface
│   │   ├── login/page.tsx       # Login page
│   │   └── register/page.tsx    # Registration page
│   ├── components/
│   │   ├── ChatUI.tsx           # Main chat component
│   │   ├── MessageBubble.tsx    # Message display with structured parsing
│   │   └── Sidebar.tsx          # History sidebar
│   ├── lib/
│   │   └── api.ts               # Fetch-based HTTP client
│   ├── actions/
│   │   └── auth-actions.ts      # Server actions for auth
│   ├── middleware.ts            # Route protection
│   └── package.json
└── README.md
```

## Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **MongoDB** running on localhost:27017

## Setup Instructions

### 1. Clone and navigate

```bash
cd "C:/Drishti/Projects/Music"
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
# Edit .env file if needed (set OPENAI_API_KEY if you want OpenAI, set USE_OPENAI=true)

# Start the server
uvicorn app.main:app --reload --port 8000
```

On first run, the backend will:
1. Load legal documents from `data/legal_documents/`
2. Generate embeddings using sentence-transformers
3. Build and save the FAISS index

This takes 1-2 minutes on first startup. Subsequent starts load the cached index.

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

### 4. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### 5. Create a User

1. Go to http://localhost:3000/register
2. Create an account
3. Login and start chatting

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | /auth/register | No | Register new user |
| POST | /auth/login | No | Login user |
| POST | /auth/logout | No | Logout user |
| POST | /chat | Yes | Send query, get legal response |
| GET | /history | Yes | Get user's chat history |
| DELETE | /history/{id} | Yes | Delete a chat session |
| POST | /admin/upload-document | Admin | Upload new legal document |
| GET | /admin/stats | Admin | Get system statistics |
| GET | /health | No | Health check |

## Using OpenAI Instead of HuggingFace

By default, the app uses HuggingFace's `google/flan-t5-base` model (runs locally, no API key needed). For better responses:

1. Set `OPENAI_API_KEY=sk-your-key` in `backend/.env`
2. Set `USE_OPENAI=true` in `backend/.env`
3. Restart the backend

## Sample Legal Documents Included

- **IPC Key Sections** - Murder, theft, cheating, 498A, defamation, etc.
- **CrPC Basics** - FIR, bail, arrest, cognizable offences, etc.
- **Fundamental Rights** - Articles 14-32, writs, right to life, etc.
- **Consumer Protection Act 2019** - Consumer rights, filing complaints, CCPA, etc.
- **Family Law** - Hindu Marriage Act, divorce, maintenance, domestic violence, etc.
- **Cyber Law** - IT Act 2000, identity theft, cyber terrorism, DPDPA 2023, etc.
- **Labour Law** - EPF, ESI, gratuity, POSH Act, maternity benefits, etc.

## Adding New Documents

### Via API (Admin)

First, make a user an admin by setting `is_admin: true` in MongoDB:

```javascript
// In MongoDB shell
db.users.updateOne({email: "admin@example.com"}, {$set: {is_admin: true}})
```

Then upload via API:

```bash
curl -X POST http://localhost:8000/admin/upload-document \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"title": "New Law", "content": "Full text...", "category": "indian_law"}'
```

### Via File System

Add `.txt` files to `backend/data/legal_documents/`, then delete `backend/data/faiss_index/` and restart the server to rebuild the index.
