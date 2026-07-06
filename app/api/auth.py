"""
POST /auth/login    -> access + refresh tokens
POST /auth/logout   -> (stateless) client discards tokens; logged for audit
POST /auth/refresh  -> exchange refresh token for new access token
GET  /auth/me       -> current authenticated user profile
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_password, create_access_token, create_refresh_token, decode_token
from app.core.audit import log_action
from app.models.user import User, LoginHistory, UserStatus
from app.schemas.auth import LoginRequest, TokenResponse, RefreshRequest, AccessTokenResponse
from app.schemas.user import UserOut
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()

    success = bool(user and verify_password(payload.password, user.password_hash))
    db.add(
        LoginHistory(
            user_id=user.id if user else 0,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            success=success,
        )
    )
    db.commit()

    if not success:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    if user.status != UserStatus.active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is not active")

    access_token = create_access_token(user.id, extra_claims={"role": user.role.name if user.role else None})
    refresh_token = create_refresh_token(user.id)

    log_action(db, user_id=user.id, action="User logged in", table_name="users", record_id=user.id)

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=AccessTokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    try:
        data = decode_token(payload.refresh_token)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    if data.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    user = db.get(User, int(data["sub"]))
    if not user or user.status != UserStatus.active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    access_token = create_access_token(user.id, extra_claims={"role": user.role.name if user.role else None})
    return AccessTokenResponse(access_token=access_token)


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # JWTs are stateless; logout is a client-side token discard. We just audit it.
    log_action(db, user_id=current_user.id, action="User logged out", table_name="users", record_id=current_user.id)
    return {"detail": "Logged out successfully"}


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user
