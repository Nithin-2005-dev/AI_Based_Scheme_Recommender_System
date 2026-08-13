"""
User profile API endpoints.
"""

import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.config import get_settings
from app.core.security import encrypt_sensitive_field, hash_password, verify_password
from app.api.deps import get_current_user
from app.models.user import User, UserDocument
from app.schemas.user import UserProfileUpdate, UserProfileResponse, DocumentUploadResponse
from app.schemas.auth import ChangePasswordRequest, MessageResponse

settings = get_settings()
router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserProfileResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    """Get current user's profile."""
    response = UserProfileResponse.model_validate(current_user)
    response.has_aadhaar = bool(current_user.aadhaar_encrypted)
    response.has_pan = bool(current_user.pan_encrypted)
    response.profile_completion_percentage = current_user.calculate_profile_completion()
    return response


@router.put("/me", response_model=UserProfileResponse)
async def update_profile(
    update: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update user profile."""
    update_data = update.model_dump(exclude_unset=True)

    # Handle sensitive fields
    if "aadhaar" in update_data and update_data["aadhaar"]:
        current_user.aadhaar_encrypted = encrypt_sensitive_field(update_data.pop("aadhaar"))
    elif "aadhaar" in update_data:
        update_data.pop("aadhaar")

    if "pan" in update_data and update_data["pan"]:
        current_user.pan_encrypted = encrypt_sensitive_field(update_data.pop("pan"))
    elif "pan" in update_data:
        update_data.pop("pan")

    # Update all other fields
    for field, value in update_data.items():
        if hasattr(current_user, field):
            setattr(current_user, field, value)

    # Recalculate profile completion
    current_user.profile_completion_percentage = current_user.calculate_profile_completion()
    current_user.profile_completed = current_user.profile_completion_percentage >= 70.0

    response = UserProfileResponse.model_validate(current_user)
    response.has_aadhaar = bool(current_user.aadhaar_encrypted)
    response.has_pan = bool(current_user.pan_encrypted)
    return response


@router.post("/me/documents", response_model=DocumentUploadResponse)
async def upload_document(
    document_type: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a user document."""
    # Validate file type
    ext = file.filename.split(".")[-1].lower() if file.filename else ""
    if ext not in settings.allowed_file_types_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '{ext}' not allowed. Allowed: {settings.ALLOWED_FILE_TYPES}",
        )

    # Validate file size
    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE_MB}MB",
        )

    # Save file
    upload_dir = os.path.join(settings.UPLOAD_DIR, str(current_user.id))
    os.makedirs(upload_dir, exist_ok=True)
    file_name = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = os.path.join(upload_dir, file_name)

    with open(file_path, "wb") as f:
        f.write(content)

    # Create document record
    doc = UserDocument(
        user_id=current_user.id,
        document_type=document_type,
        document_name=file.filename or file_name,
        file_path=file_path,
        file_size=len(content),
        mime_type=file.content_type,
    )
    db.add(doc)
    await db.flush()

    return DocumentUploadResponse.model_validate(doc)


@router.get("/me/documents", response_model=list[DocumentUploadResponse])
async def get_documents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user's uploaded documents."""
    result = await db.execute(
        select(UserDocument).where(UserDocument.user_id == current_user.id)
    )
    docs = result.scalars().all()
    return [DocumentUploadResponse.model_validate(d) for d in docs]


@router.post("/me/change-password", response_model=MessageResponse)
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change user's password."""
    if not verify_password(request.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    current_user.hashed_password = hash_password(request.new_password)
    return MessageResponse(message="Password changed successfully")


@router.delete("/me", response_model=MessageResponse)
async def delete_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete user account."""
    await db.delete(current_user)
    return MessageResponse(message="Account deleted successfully")
