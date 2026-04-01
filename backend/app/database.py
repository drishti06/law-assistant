import json
import os
from pathlib import Path
from app.utils.logger import logger

DATA_DIR = Path(__file__).parent.parent / "data" / "db"
DATA_DIR.mkdir(parents=True, exist_ok=True)

USERS_FILE = DATA_DIR / "users.json"
SESSIONS_FILE = DATA_DIR / "chat_sessions.json"
DOCUMENTS_FILE = DATA_DIR / "legal_documents.json"


def _read_json(filepath: Path) -> list[dict]:
    if not filepath.exists():
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def _write_json(filepath: Path, data: list[dict]):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str, ensure_ascii=False)


# --- Users ---

def get_user_by_email(email: str) -> dict | None:
    users = _read_json(USERS_FILE)
    for u in users:
        if u["email"] == email:
            return u
    return None


def create_user(user_doc: dict):
    users = _read_json(USERS_FILE)
    users.append(user_doc)
    _write_json(USERS_FILE, users)
    logger.info(f"User saved: {user_doc['email']}")


def count_users() -> int:
    return len(_read_json(USERS_FILE))


# --- Chat Sessions ---

def get_sessions_by_email(email: str, limit: int = 50) -> list[dict]:
    sessions = _read_json(SESSIONS_FILE)
    user_sessions = [s for s in sessions if s["user_email"] == email]
    user_sessions.sort(key=lambda s: s.get("updated_at", ""), reverse=True)
    return user_sessions[:limit]


def get_session_by_id(session_id: str) -> dict | None:
    sessions = _read_json(SESSIONS_FILE)
    for s in sessions:
        if s["id"] == session_id:
            return s
    return None


def find_today_session(email: str, today_str: str) -> dict | None:
    sessions = _read_json(SESSIONS_FILE)
    for s in sessions:
        if s["user_email"] == email and s.get("updated_at", "").startswith(today_str):
            return s
    return None


def upsert_session(session: dict):
    sessions = _read_json(SESSIONS_FILE)
    for i, s in enumerate(sessions):
        if s["id"] == session["id"]:
            sessions[i] = session
            _write_json(SESSIONS_FILE, sessions)
            return
    sessions.append(session)
    _write_json(SESSIONS_FILE, sessions)


def delete_session(session_id: str, email: str) -> bool:
    sessions = _read_json(SESSIONS_FILE)
    new_sessions = [s for s in sessions if not (s["id"] == session_id and s["user_email"] == email)]
    if len(new_sessions) == len(sessions):
        return False
    _write_json(SESSIONS_FILE, new_sessions)
    return True


def count_sessions() -> int:
    return len(_read_json(SESSIONS_FILE))


# --- Legal Documents ---

def save_legal_document(doc: dict):
    docs = _read_json(DOCUMENTS_FILE)
    docs.append(doc)
    _write_json(DOCUMENTS_FILE, docs)


def count_documents() -> int:
    return len(_read_json(DOCUMENTS_FILE))
