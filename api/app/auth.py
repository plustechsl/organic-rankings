from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.ratelimit import (
    clear_login_failures,
    limit_login,
    limit_register,
    login_locked_retry_after,
    register_login_failure,
)
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    ProfileUpdate,
    RegisterRequest,
)
from app.security import hash_password, verify_password, create_access_token
from app.turnstile import verify_turnstile


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post("/register")
def register(
    data: RegisterRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    limit_register(request)
    verify_turnstile(data.turnstile_token, request)

    existing_user = db.scalar(
        select(User).where(
            (User.username == data.username)
            | (User.email == data.email)
        )
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already exists",
        )

    user = User(
        username=data.username,
        email=data.email,
        password_hash=hash_password(data.password),
        role="user",
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "access_token": create_access_token(user.id),
        "token_type": "bearer",
    }


@router.post("/login")
def login(
    data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    limit_login(request)

    locked_for = login_locked_retry_after(data.username)

    if locked_for is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed attempts. Please try again later.",
            headers={"Retry-After": str(locked_for)},
        )

    verify_turnstile(data.turnstile_token, request)

    user = db.scalar(
        select(User).where(
            User.username == data.username
        )
    )

    if not user or not verify_password(
        data.password,
        user.password_hash,
    ):
        register_login_failure(data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    clear_login_failures(data.username)

    token = create_access_token(user.id)

    return {
        "access_token": token,
        "token_type": "bearer",
    }


@router.get("/me")
def get_me(
    current_user: User = Depends(get_current_user),
):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
    }


@router.patch("/me")
def update_me(
    payload: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.username is not None and payload.username != current_user.username:
        existing = db.scalar(
            select(User).where(User.username == payload.username)
        )

        if existing:
            raise HTTPException(
                status_code=409,
                detail="Username already taken",
            )

        current_user.username = payload.username

    if payload.email is not None and payload.email != current_user.email:
        existing = db.scalar(
            select(User).where(User.email == payload.email)
        )

        if existing:
            raise HTTPException(
                status_code=409,
                detail="Email already taken",
            )

        current_user.email = payload.email

    db.commit()
    db.refresh(current_user)

    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
    }


@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Current password is incorrect",
        )

    current_user.password_hash = hash_password(payload.new_password)

    db.commit()

    return {
        "message": "Password updated successfully",
    }
