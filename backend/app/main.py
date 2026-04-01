import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.routes import auth, chat, admin
from app.services.rag_service import initialize_rag
from app.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Legal Chatbot API...")
    logger.info("Initializing RAG system...")
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, initialize_rag)
    logger.info("RAG system initialized")
    yield
    logger.info("Legal Chatbot API shut down")


app = FastAPI(
    title="Legal Chatbot API - Indian Law",
    description="AI-powered legal assistant specialized in Indian law",
    version="1.0.0",
    lifespan=lifespan,
)

settings = get_settings()
origins = [o.strip() for o in settings.cors_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(admin.router)


@app.get("/")
async def root():
    return {"message": "Legal Chatbot API is running", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
