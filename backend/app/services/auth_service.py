"""
Authentication service: signup, login, token management, password reset, email verification.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from app.models.user import User, RefreshToken
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    decode_refresh_token,
    create_email_verification_token, decode_email_verification_token,
    create_password_reset_token, decode_password_reset_token,
    generate_random_token,
)
from app.core.config import get_settings
from app.schemas.auth import SignupRequest, TokenResponse, UserBrief

settings = get_settings()


class AuthService:
    """Handles all authentication operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def signup(self, request: SignupRequest) -> dict:
        """Register a new user with email verification."""
        # Check if email exists
        result = await self.db.execute(
            select(User).where(User.email == request.email)
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise ValueError("Email already registered")

        # Create user
        user = User(
            email=request.email,
            hashed_password=hash_password(request.password),
            full_name=request.full_name,
            role=request.role if request.role in ("citizen", "admin") else "citizen",
            is_email_verified=not settings.EMAIL_VERIFICATION_ENABLED,
        )

        if settings.EMAIL_VERIFICATION_ENABLED:
            user.email_verification_token = create_email_verification_token(request.email)

        self.db.add(user)
        await self.db.flush()

        # Generate tokens
        tokens = await self._create_tokens(user)

        logger.info(f"New user registered: {request.email}")
        return tokens

    async def login(self, email: str, password: str) -> dict:
        """Authenticate user and return tokens."""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()

        if not user or not verify_password(password, user.hashed_password):
            raise ValueError("Invalid email or password")

        # Update last login
        user.last_login = datetime.now(timezone.utc)

        tokens = await self._create_tokens(user)

        logger.info(f"User logged in: {email}")
        return tokens

    async def refresh_tokens(self, refresh_token_str: str) -> dict:
        """Refresh access token using refresh token."""
        payload = decode_refresh_token(refresh_token_str)
        if not payload:
            raise ValueError("Invalid refresh token")

        user_id = payload.get("sub")

        # Check if token exists and is not revoked
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.token == refresh_token_str,
                RefreshToken.is_revoked == False,
            )
        )
        stored_token = result.scalar_one_or_none()
        if not stored_token:
            raise ValueError("Refresh token not found or revoked")

        # Revoke old token
        stored_token.is_revoked = True

        # Get user
        result = await self.db.execute(select(User).where(User.id == int(user_id)))
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("User not found")

        # Generate new tokens
        tokens = await self._create_tokens(user)
        return tokens

    async def verify_email(self, token: str) -> bool:
        """Verify user's email address."""
        email = decode_email_verification_token(token)
        if not email:
            raise ValueError("Invalid or expired verification token")

        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("User not found")

        user.is_email_verified = True
        user.email_verification_token = None

        logger.info(f"Email verified: {email}")
        return True

    async def forgot_password(self, email: str) -> str:
        """Generate password reset token."""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        if not user:
            # Return success even if user not found (security best practice)
            return "If the email exists, a reset link has been sent"

        token = create_password_reset_token(email)
        reset_url = f"{settings.FRONTEND_URL}/auth/reset-password?token={token}"

        # In production, send email here
        logger.info(f"Password reset requested for: {email}. Reset URL: {reset_url}")

        return "If the email exists, a reset link has been sent"

    async def reset_password(self, token: str, new_password: str) -> bool:
        """Reset password using reset token."""
        email = decode_password_reset_token(token)
        if not email:
            raise ValueError("Invalid or expired reset token")

        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("User not found")

        user.hashed_password = hash_password(new_password)

        # Revoke all refresh tokens
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user.id,
                RefreshToken.is_revoked == False,
            )
        )
        for rt in result.scalars():
            rt.is_revoked = True

        logger.info(f"Password reset for: {email}")
        return True

    async def logout(self, user_id: int, refresh_token_str: Optional[str] = None) -> bool:
        """Revoke refresh token(s) on logout."""
        if refresh_token_str:
            result = await self.db.execute(
                select(RefreshToken).where(
                    RefreshToken.token == refresh_token_str,
                    RefreshToken.user_id == user_id,
                )
            )
            token = result.scalar_one_or_none()
            if token:
                token.is_revoked = True
        else:
            # Revoke all tokens for user
            result = await self.db.execute(
                select(RefreshToken).where(
                    RefreshToken.user_id == user_id,
                    RefreshToken.is_revoked == False,
                )
            )
            for rt in result.scalars():
                rt.is_revoked = True

        return True

    async def _create_tokens(self, user: User) -> dict:
        """Create access and refresh token pair."""
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})

        # Store refresh token
        rt = RefreshToken(
            user_id=user.id,
            token=refresh_token,
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
        )
        self.db.add(rt)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "is_email_verified": user.is_email_verified,
                "profile_completed": user.profile_completed,
            },
        }
