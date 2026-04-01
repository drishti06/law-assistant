from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Response
from app.models.user import UserCreate, UserLogin, UserResponse
from app.utils.auth import hash_password, verify_password, create_access_token
from app.database import get_user_by_email, create_user
from app.utils.logger import logger

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate):
    existing = get_user_by_email(user.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    now = datetime.utcnow().isoformat()
    user_doc = {
        "name": user.name,
        "email": user.email,
        "hashed_password": hash_password(user.password),
        "created_at": now,
        "is_admin": False,
    }
    create_user(user_doc)
    logger.info(f"New user registered: {user.email}")

    return UserResponse(name=user.name, email=user.email, created_at=now)


@router.post("/login")
async def login(user: UserLogin, response: Response):
    db_user = get_user_by_email(user.email)

    if not db_user or not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token({"sub": user.email, "name": db_user["name"]})

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=86400,
        samesite="lax",
        secure=False,
    )

    logger.info(f"User logged in: {user.email}")
    return {
        "message": "Login successful",
        "token": token,
        "user": {"name": db_user["name"], "email": db_user["email"]},
    }


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out successfully"}
