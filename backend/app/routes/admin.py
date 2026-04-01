import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from app.models.chat import DocumentUpload
from app.services.rag_service import add_document, add_pdf_document, _index, _chunks
from app.utils.auth import get_current_user
from app.database import get_user_by_email, save_legal_document, count_users, count_sessions, count_documents
from app.utils.logger import logger

router = APIRouter(prefix="/admin", tags=["Admin"])

UPLOAD_DIR = os.path.join("data", "legal_documents")


@router.post("/upload-document")
async def upload_document(
    doc: DocumentUpload,
    user_email: str = Depends(get_current_user),
):
    user = get_user_by_email(user_email)
    if not user or not user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    add_document(doc.title, doc.content, doc.category)

    save_legal_document({
        "title": doc.title,
        "content": doc.content,
        "category": doc.category,
        "uploaded_by": user_email,
    })

    logger.info(f"Document '{doc.title}' uploaded by {user_email}")
    return {"message": f"Document '{doc.title}' added to vector database"}


@router.post("/upload-pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    title: str = Form(default=""),
    category: str = Form(default="indian_law"),
    user_email: str = Depends(get_current_user),
):
    user = get_user_by_email(user_email)
    if not user or not user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are accepted",
        )

    # Save PDF to legal_documents directory
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    safe_name = file.filename.replace(" ", "_")
    filepath = os.path.join(UPLOAD_DIR, safe_name)

    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)

    logger.info(f"PDF saved to {filepath}")

    # Extract text and add to FAISS index
    doc_title = title if title else safe_name.replace(".pdf", "").replace("_", " ").title()
    char_count = add_pdf_document(filepath, doc_title, category)

    if char_count == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not extract any text from the PDF",
        )

    save_legal_document({
        "title": doc_title,
        "content": f"[PDF file: {safe_name}, {char_count} characters extracted]",
        "category": category,
        "uploaded_by": user_email,
    })

    return {
        "message": f"PDF '{doc_title}' processed and added to vector database",
        "filename": safe_name,
        "characters_extracted": char_count,
    }


@router.get("/stats")
async def get_stats(user_email: str = Depends(get_current_user)):
    user = get_user_by_email(user_email)
    if not user or not user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    index_size = _index.ntotal if _index else 0
    chunk_count = len(_chunks)

    return {
        "users": count_users(),
        "chat_sessions": count_sessions(),
        "documents_in_db": count_documents(),
        "vectors_in_index": index_size,
        "chunks": chunk_count,
    }
