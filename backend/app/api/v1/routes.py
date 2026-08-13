"""
Recommendation, Eligibility, Search, Notification, Chatbot, Admin, Analytics, Translate API routes.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from app.core.database import get_db
from app.api.deps import get_current_user, get_admin_user
from app.models.user import User
from app.models.scheme import Scheme
from app.models.notification import Notification
from app.services.recommendation_engine import RecommendationEngine
from app.services.eligibility_checker import EligibilityChecker
from app.services.search_engine import SearchEngine
from app.services.notification_engine import NotificationEngine
from app.services.rag_chatbot import RAGChatbot, SUPPORTED_CHAT_LANGUAGES
from app.services.analytics_service import AnalyticsService
from app.services.translation_service import translation_service
from app.schemas.scheme import (
    EligibilityCheckRequest, SearchRequest,
    SendNotificationRequest, ChatRequest, ChatResponse,
    TranslateRequest, TranslateResponse,
)
from app.schemas.auth import MessageResponse

# ===== Recommendations Router =====
recommendations_router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@recommendations_router.get("")
async def get_recommendations(
    top_k: int = Query(5, ge=1, le=20),
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get personalized scheme recommendations with XAI explanations."""
    engine = RecommendationEngine(db)
    results = await engine.get_recommendations(current_user, top_k, category)

    recommendations = []
    for r in results:
        scheme = r["scheme"]
        recommendations.append({
            "scheme": {
                "id": scheme.id,
                "scheme_name": scheme.scheme_name,
                "slug": scheme.slug,
                "details": (scheme.details or "")[:500],
                "benefits": (scheme.benefits or "")[:500],
                "eligibility": (scheme.eligibility or "")[:500],
                "level": scheme.level,
                "scheme_category": scheme.scheme_category,
                "application_link": scheme.application_link or scheme.official_website,
            },
            "score": r["score"],
            "confidence": r["confidence"],
            "reasons": r["reasons"],
            "matched_conditions": r["matched_conditions"],
            "failed_conditions": r["failed_conditions"],
            "eligibility_probability": r["eligibility_probability"],
            "eligibility_status": "eligible" if r["eligibility_probability"] >= 0.5 else "not_eligible",
        })

    return {
        "recommendations": recommendations,
        "total_evaluated": len(results),
        "user_profile_summary": {
            "age": current_user.age,
            "gender": current_user.gender,
            "state": current_user.state,
            "category": current_user.category,
            "occupation": current_user.occupation,
            "income": current_user.income,
            "education": current_user.education,
            "profile_completed": current_user.profile_completed,
        },
    }


# ===== Eligibility Router =====
eligibility_router = APIRouter(prefix="/eligibility", tags=["Eligibility"])


@eligibility_router.get("")
async def get_full_eligibility(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    category: Optional[str] = None,
    state: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Evaluate ALL schemes for the authenticated user. Returns eligible + ineligible counts and lists."""
    checker = EligibilityChecker(db)
    result = await checker.check_all_schemes(
        user=current_user,
        page=page,
        page_size=page_size,
        search=search,
        category=category,
        state_filter=state,
    )
    return result


@eligibility_router.get("/eligible")
async def get_eligible_schemes(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    category: Optional[str] = None,
    state: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get only ELIGIBLE schemes for the authenticated user."""
    checker = EligibilityChecker(db)
    result = await checker.check_all_schemes(
        user=current_user,
        page=page,
        page_size=page_size,
        search=search,
        category=category,
        state_filter=state,
        eligibility_filter="eligible",
    )
    return result


@eligibility_router.get("/ineligible")
async def get_ineligible_schemes(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    category: Optional[str] = None,
    state: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get only NOT ELIGIBLE schemes for the authenticated user."""
    checker = EligibilityChecker(db)
    result = await checker.check_all_schemes(
        user=current_user,
        page=page,
        page_size=page_size,
        search=search,
        category=category,
        state_filter=state,
        eligibility_filter="ineligible",
    )
    return result


@eligibility_router.post("/check")
async def check_eligibility(
    request: EligibilityCheckRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Check eligibility for a specific scheme."""
    try:
        checker = EligibilityChecker(db)
        result = await checker.check_eligibility(current_user, request.scheme_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@eligibility_router.get("/check/{scheme_id}")
async def check_eligibility_by_id(
    scheme_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Check eligibility by scheme ID (GET)."""
    try:
        checker = EligibilityChecker(db)
        result = await checker.check_eligibility(current_user, scheme_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ===== Search Router =====
search_router = APIRouter(prefix="/search", tags=["Search"])


@search_router.get("")
async def search_schemes(
    q: str = Query("", max_length=500),
    category: Optional[str] = None,
    level: Optional[str] = None,
    state: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Search schemes with filters."""
    engine = SearchEngine(db)
    results = await engine.search(
        query=q,
        category=category,
        level=level,
        state=state,
        page=page,
        page_size=page_size,
    )

    return {
        "results": [
            {
                "id": s.id,
                "scheme_name": s.scheme_name,
                "slug": s.slug,
                "details": (s.details or "")[:300],
                "benefits": (s.benefits or "")[:300],
                "level": s.level,
                "scheme_category": s.scheme_category,
                "view_count": s.view_count,
            }
            for s in results["results"]
        ],
        "total": results["total"],
        "page": results["page"],
        "page_size": results["page_size"],
        "query": results["query"],
        "suggestions": results["suggestions"],
    }


@search_router.get("/autocomplete")
async def autocomplete(
    q: str = Query("", min_length=2, max_length=100),
    db: AsyncSession = Depends(get_db),
):
    """Get autocomplete suggestions."""
    engine = SearchEngine(db)
    return await engine.autocomplete(q)


# ===== Notifications Router =====
notifications_router = APIRouter(prefix="/notifications", tags=["Notifications"])


@notifications_router.get("")
async def get_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    unread_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user's notifications."""
    engine = NotificationEngine(db)
    result = await engine.get_user_notifications(
        current_user.id, page, page_size, unread_only
    )

    return {
        "notifications": [
            {
                "id": n.id,
                "title": n.title,
                "message": n.message,
                "notification_type": n.notification_type,
                "channel": n.channel,
                "priority": n.priority,
                "scheme_name": n.scheme_name,
                "scheme_id": n.scheme_id,
                "is_read": n.is_read,
                "change_details": n.change_details,
                "created_at": n.created_at.isoformat() if n.created_at else None,
            }
            for n in result["notifications"]
        ],
        "total": result["total"],
        "unread_count": result["unread_count"],
    }


@notifications_router.get("/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get unread notification count (lightweight for bell badge)."""
    result = await db.execute(
        select(func.count(Notification.id)).where(
            Notification.user_id == current_user.id,
            Notification.is_read == False,
        )
    )
    count = result.scalar() or 0
    return {"unread_count": count}


@notifications_router.put("/{notification_id}/read", response_model=MessageResponse)
async def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark notification as read."""
    engine = NotificationEngine(db)
    await engine.mark_as_read(notification_id, current_user.id)
    return MessageResponse(message="Notification marked as read")


@notifications_router.put("/read-all", response_model=MessageResponse)
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark all notifications as read."""
    engine = NotificationEngine(db)
    count = await engine.mark_all_read(current_user.id)
    return MessageResponse(message=f"{count} notifications marked as read")


@notifications_router.delete("/{notification_id}", response_model=MessageResponse)
async def delete_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete/dismiss a notification."""
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
    )
    notification = result.scalar_one_or_none()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    await db.delete(notification)
    return MessageResponse(message="Notification deleted")


# ===== Chatbot Router =====
chatbot_router = APIRouter(prefix="/chatbot", tags=["Chatbot"])


@chatbot_router.post("", response_model=ChatResponse)
async def ask_chatbot(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Ask the AI chatbot a question about government schemes."""
    chatbot = RAGChatbot(db)
    result = await chatbot.ask(
        user_id=current_user.id,
        message=request.message,
        session_id=request.session_id,
        language=request.language,
        user=current_user,
    )
    return ChatResponse(**result)


@chatbot_router.get("/languages")
async def get_chatbot_languages():
    """Get supported chatbot languages (exactly 3: English, Telugu, Hindi)."""
    return {
        "languages": [
            {"code": code, "name": name}
            for code, name in SUPPORTED_CHAT_LANGUAGES.items()
        ]
    }


@chatbot_router.get("/history/{session_id}")
async def get_chat_history(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get chat history for a session."""
    chatbot = RAGChatbot(db)
    return await chatbot.get_chat_history(current_user.id, session_id)


# ===== Admin Router =====
admin_router = APIRouter(prefix="/admin", tags=["Admin"])


@admin_router.get("/users")
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """List all users (admin only)."""
    query = select(User)
    count_query = select(func.count(User.id))

    if search:
        filter_cond = User.email.ilike(f"%{search}%")
        query = query.where(filter_cond)
        count_query = count_query.where(filter_cond)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    users = result.scalars().all()

    return {
        "users": [
            {
                "id": u.id,
                "email": u.email,
                "full_name": u.full_name,
                "role": u.role,
                "state": u.state,
                "is_email_verified": u.is_email_verified,
                "profile_completed": u.profile_completed,
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "last_login": u.last_login.isoformat() if u.last_login else None,
            }
            for u in users
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@admin_router.post("/notifications/send", response_model=MessageResponse)
async def send_notification(
    request: SendNotificationRequest,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Send notification to users (admin only)."""
    engine = NotificationEngine(db)
    count = await engine.create_bulk_notification(
        title=request.title,
        message=request.message,
        notification_type=request.notification_type,
        target_user_ids=request.target_users,
        scheme_id=request.scheme_id,
        priority=request.priority,
    )
    return MessageResponse(message=f"Notification sent to {count} users")


@admin_router.get("/scheme-versions/{scheme_id}")
async def get_scheme_versions(
    scheme_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Get version history for a scheme (admin only)."""
    from app.services.rule_change_detector import RuleChangeDetector
    detector = RuleChangeDetector(db)
    return await detector.get_version_history(scheme_id)


# ===== Analytics Router =====
analytics_router = APIRouter(prefix="/analytics", tags=["Analytics"])


@analytics_router.get("/dashboard")
async def get_dashboard(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Get full analytics dashboard data (admin only)."""
    service = AnalyticsService(db)
    return await service.get_full_dashboard()


@analytics_router.get("/stats")
async def get_stats(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Get basic stats."""
    service = AnalyticsService(db)
    return await service.get_dashboard_stats()


# ===== Translation Router =====
translate_router = APIRouter(prefix="/translate", tags=["Translation"])


@translate_router.get("/languages")
async def get_languages():
    """Get all supported languages."""
    return translation_service.get_supported_languages()


@translate_router.get("/ui/{language}")
async def get_ui_translations(language: str):
    """Get UI translations for a language."""
    return translation_service.get_ui_translations(language)


@translate_router.post("", response_model=TranslateResponse)
async def translate_text(request: TranslateRequest):
    """Translate text to target language."""
    result = await translation_service.translate_text(
        text=request.text,
        target_language=request.target_language,
        source_language=request.source_language,
    )
    return TranslateResponse(**result)
