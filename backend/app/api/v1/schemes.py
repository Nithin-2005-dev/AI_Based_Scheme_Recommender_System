"""
Scheme API endpoints: list, detail, CRUD, search, categories.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from app.core.database import get_db
from app.api.deps import get_current_user, get_admin_user, get_optional_user
from app.models.user import User
from app.models.scheme import Scheme
from app.models.notification import SavedScheme, ApplicationTracker
from app.schemas.scheme import (
    SchemeResponse, SchemeListResponse, SchemeCreateRequest,
    SchemeUpdateRequest, SaveSchemeRequest, SavedSchemeResponse,
    ApplicationUpdateRequest, ApplicationResponse,
)
from app.schemas.auth import MessageResponse
from app.services.search_engine import SearchEngine

router = APIRouter(prefix="/schemes", tags=["Schemes"])


@router.get("", response_model=SchemeListResponse)
async def list_schemes(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    category: Optional[str] = None,
    level: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List schemes with pagination and filters."""
    query = select(Scheme).where(Scheme.is_active == True)
    count_query = select(func.count(Scheme.id)).where(Scheme.is_active == True)

    if category:
        query = query.where(Scheme.scheme_category.ilike(f"%{category}%"))
        count_query = count_query.where(Scheme.scheme_category.ilike(f"%{category}%"))

    if level and level in ("Central", "State"):
        query = query.where(Scheme.level == level)
        count_query = count_query.where(Scheme.level == level)

    if search:
        search_filter = Scheme.scheme_name.ilike(f"%{search}%")
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(Scheme.scheme_name).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    schemes = result.scalars().all()

    total_pages = (total + page_size - 1) // page_size

    return SchemeListResponse(
        schemes=[_scheme_to_response(s) for s in schemes],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/categories")
async def get_categories(db: AsyncSession = Depends(get_db)):
    """Get all scheme categories with counts."""
    engine = SearchEngine(db)
    return await engine.get_categories()


@router.get("/popular")
async def get_popular_schemes(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Get most popular schemes."""
    engine = SearchEngine(db)
    schemes = await engine.get_popular_schemes(limit)
    return [_scheme_to_response(s) for s in schemes]


@router.get("/{slug}", response_model=SchemeResponse)
async def get_scheme(
    slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """Get scheme by slug."""
    result = await db.execute(select(Scheme).where(Scheme.slug == slug))
    scheme = result.scalar_one_or_none()
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")

    # Increment view count
    scheme.view_count += 1

    return _scheme_to_response(scheme)


@router.post("", response_model=SchemeResponse, status_code=status.HTTP_201_CREATED)
async def create_scheme(
    request: SchemeCreateRequest,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new scheme (admin only)."""
    existing = await db.execute(select(Scheme).where(Scheme.slug == request.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Slug already exists")

    scheme = Scheme(
        scheme_name=request.scheme_name,
        slug=request.slug,
        details=request.details,
        benefits=request.benefits,
        eligibility=request.eligibility,
        application_process=request.application_process,
        documents_required=request.documents_required,
        level=request.level,
        scheme_category=request.scheme_category,
        official_website=request.official_website,
        application_link=request.application_link,
        deadline=request.deadline,
    )
    db.add(scheme)
    await db.flush()
    return _scheme_to_response(scheme)


@router.put("/{scheme_id}", response_model=SchemeResponse)
async def update_scheme(
    scheme_id: int,
    request: SchemeUpdateRequest,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a scheme (admin only). Triggers rule change detection."""
    result = await db.execute(select(Scheme).where(Scheme.id == scheme_id))
    scheme = result.scalar_one_or_none()
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")

    # Detect rule changes
    from app.services.rule_change_detector import RuleChangeDetector
    detector = RuleChangeDetector(db)
    await detector.detect_changes(
        scheme_id=scheme_id,
        new_eligibility=request.eligibility,
        new_benefits=request.benefits,
        new_documents=request.documents_required,
        new_details=request.details,
        admin_user_id=admin.id,
    )

    # Update other fields
    update_data = request.model_dump(exclude_unset=True, exclude={"eligibility", "benefits", "documents_required", "details"})
    for field, value in update_data.items():
        if hasattr(scheme, field):
            setattr(scheme, field, value)

    return _scheme_to_response(scheme)


@router.delete("/{scheme_id}", response_model=MessageResponse)
async def delete_scheme(
    scheme_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Soft delete a scheme (admin only)."""
    result = await db.execute(select(Scheme).where(Scheme.id == scheme_id))
    scheme = result.scalar_one_or_none()
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")
    scheme.is_active = False
    return MessageResponse(message="Scheme deleted successfully")


# ===== Saved Schemes =====
@router.post("/save", response_model=MessageResponse)
async def save_scheme(
    request: SaveSchemeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Save/bookmark a scheme."""
    existing = await db.execute(
        select(SavedScheme).where(
            SavedScheme.user_id == current_user.id,
            SavedScheme.scheme_id == request.scheme_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Scheme already saved")

    saved = SavedScheme(
        user_id=current_user.id,
        scheme_id=request.scheme_id,
        notes=request.notes,
        notify_on_changes=request.notify_on_changes,
    )
    db.add(saved)
    return MessageResponse(message="Scheme saved successfully")


@router.get("/saved/list")
async def get_saved_schemes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user's saved schemes."""
    result = await db.execute(
        select(SavedScheme)
        .where(SavedScheme.user_id == current_user.id)
        .order_by(SavedScheme.saved_at.desc())
    )
    saved = result.scalars().all()

    response = []
    for s in saved:
        scheme_result = await db.execute(select(Scheme).where(Scheme.id == s.scheme_id))
        scheme = scheme_result.scalar_one_or_none()
        if scheme:
            response.append({
                "id": s.id,
                "scheme": _scheme_to_response(scheme),
                "notes": s.notes,
                "notify_on_changes": s.notify_on_changes,
                "saved_at": s.saved_at.isoformat() if s.saved_at else None,
            })

    return response


@router.delete("/save/{scheme_id}", response_model=MessageResponse)
async def unsave_scheme(
    scheme_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a saved scheme."""
    result = await db.execute(
        select(SavedScheme).where(
            SavedScheme.user_id == current_user.id,
            SavedScheme.scheme_id == scheme_id,
        )
    )
    saved = result.scalar_one_or_none()
    if saved:
        await db.delete(saved)
    return MessageResponse(message="Scheme removed from saved list")


# ===== Application Tracker =====
@router.post("/apply/{scheme_id}", response_model=ApplicationResponse)
async def start_application(
    scheme_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start tracking an application."""
    scheme_result = await db.execute(select(Scheme).where(Scheme.id == scheme_id))
    scheme = scheme_result.scalar_one_or_none()
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")

    # Check for existing application
    existing = await db.execute(
        select(ApplicationTracker).where(
            ApplicationTracker.user_id == current_user.id,
            ApplicationTracker.scheme_id == scheme_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Application already exists")

    app = ApplicationTracker(
        user_id=current_user.id,
        scheme_id=scheme_id,
        status="not_started",
    )
    db.add(app)
    await db.flush()

    # Increment application count
    scheme.application_count += 1

    return ApplicationResponse(
        id=app.id,
        scheme_id=scheme_id,
        scheme_name=scheme.scheme_name,
        status=app.status,
        missing_documents=[],
        created_at=app.created_at,
        updated_at=app.updated_at,
    )


@router.get("/applications/list")
async def get_applications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user's applications."""
    result = await db.execute(
        select(ApplicationTracker)
        .where(ApplicationTracker.user_id == current_user.id)
        .order_by(ApplicationTracker.created_at.desc())
    )
    apps = result.scalars().all()

    response = []
    for app in apps:
        scheme_result = await db.execute(select(Scheme).where(Scheme.id == app.scheme_id))
        scheme = scheme_result.scalar_one_or_none()
        response.append({
            "id": app.id,
            "scheme_id": app.scheme_id,
            "scheme_name": scheme.scheme_name if scheme else "Unknown",
            "status": app.status,
            "application_date": app.application_date.isoformat() if app.application_date else None,
            "reference_number": app.reference_number,
            "eligibility_status": app.eligibility_status,
            "eligibility_score": app.eligibility_score,
            "missing_documents": app.missing_documents or [],
            "created_at": app.created_at.isoformat() if app.created_at else None,
            "updated_at": app.updated_at.isoformat() if app.updated_at else None,
        })

    return response


def _scheme_to_response(scheme: Scheme) -> SchemeResponse:
    """Convert Scheme model to response schema."""
    return SchemeResponse(
        id=scheme.id,
        scheme_name=scheme.scheme_name,
        slug=scheme.slug,
        details=scheme.details,
        benefits=scheme.benefits,
        eligibility=scheme.eligibility,
        application_process=scheme.application_process,
        documents_required=scheme.documents_required,
        level=scheme.level,
        scheme_category=scheme.scheme_category,
        tags=[],
        official_website=scheme.official_website,
        application_link=scheme.application_link,
        deadline=scheme.deadline,
        is_active=scheme.is_active,
        view_count=scheme.view_count,
        version=scheme.version,
        created_at=scheme.created_at,
        updated_at=scheme.updated_at,
    )
