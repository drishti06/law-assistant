import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from app.models.chat import ChatRequest, ChatResponse, ChatMessage, HistoryResponse
from app.services.rag_service import retrieve
from app.services.llm_service import generate_response
from app.utils.auth import get_current_user
from app.database import (
    find_today_session, upsert_session, get_sessions_by_email, delete_session,
)
from app.utils.logger import logger

router = APIRouter(tags=["Chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, user_email: str = Depends(get_current_user)):
    logger.info(f"Chat request from {user_email}: {request.query[:80]}...")

    # RAG: retrieve relevant context
    context_chunks = retrieve(request.query, top_k=5)
    sources = list({chunk["source"] for chunk in context_chunks})

    # Generate LLM response
    result = await generate_response(request.query, context_chunks, request.language)

    # Save to JSON db
    now = datetime.utcnow()
    now_str = now.isoformat()
    today_str = now.strftime("%Y-%m-%d")

    user_message = {"role": "user", "content": request.query, "timestamp": now_str}
    assistant_message = {"role": "assistant", "content": result["answer"], "timestamp": now_str}

    session = find_today_session(user_email, today_str)

    if session:
        session["messages"].append(user_message)
        session["messages"].append(assistant_message)
        session["updated_at"] = now_str
    else:
        session = {
            "id": uuid.uuid4().hex,
            "user_email": user_email,
            "messages": [user_message, assistant_message],
            "created_at": now_str,
            "updated_at": now_str,
        }

    upsert_session(session)
    logger.info(f"Response generated for {user_email}")

    return ChatResponse(
        answer=result["answer"],
        short_answer=result["short_answer"],
        explanation=result["explanation"],
        relevant_law=result["relevant_law"],
        next_steps=result["next_steps"],
        disclaimer=result["disclaimer"],
        sources=sources,
    )


@router.get("/history", response_model=list[HistoryResponse])
async def get_history(user_email: str = Depends(get_current_user)):
    sessions = get_sessions_by_email(user_email)

    result = []
    for session in sessions:
        messages = []
        for msg in session.get("messages", []):
            messages.append(
                ChatMessage(
                    role=msg["role"],
                    content=msg["content"],
                    timestamp=msg.get("timestamp", session["created_at"]),
                )
            )
        result.append(
            HistoryResponse(
                session_id=session["id"],
                messages=messages,
                created_at=session["created_at"],
                updated_at=session["updated_at"],
            )
        )

    logger.info(f"History fetched for {user_email}: {len(result)} sessions")
    return result


@router.delete("/history/{session_id}")
async def delete_session_route(session_id: str, user_email: str = Depends(get_current_user)):
    deleted = delete_session(session_id, user_email)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return {"message": "Session deleted"}
