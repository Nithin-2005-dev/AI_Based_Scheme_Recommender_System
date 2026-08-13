"""
Analytics Service for dashboard statistics and charts data.
"""

from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from loguru import logger

from app.models.user import User
from app.models.scheme import Scheme
from app.models.notification import (
    Notification, ApplicationTracker, SavedScheme, AnalyticsEvent,
)


class AnalyticsService:
    """Provides analytics data for admin and citizen dashboards."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_dashboard_stats(self) -> dict:
        """Get main dashboard statistics."""
        total_users = await self._count(User)
        total_schemes = await self._count(Scheme, Scheme.is_active == True)

        central_result = await self.db.execute(
            select(func.count(Scheme.id)).where(Scheme.level == "Central", Scheme.is_active == True)
        )
        total_central = central_result.scalar() or 0

        state_result = await self.db.execute(
            select(func.count(Scheme.id)).where(Scheme.level == "State", Scheme.is_active == True)
        )
        total_state = state_result.scalar() or 0

        # Unique categories
        cat_result = await self.db.execute(
            select(func.count(func.distinct(Scheme.scheme_category))).where(Scheme.is_active == True)
        )
        total_categories = cat_result.scalar() or 0

        total_notifications = await self._count(Notification)
        total_applications = await self._count(ApplicationTracker)

        # Active users today
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        active_result = await self.db.execute(
            select(func.count(User.id)).where(User.last_login >= today_start)
        )
        active_today = active_result.scalar() or 0

        return {
            "total_users": total_users,
            "total_schemes": total_schemes,
            "total_central": total_central,
            "total_state": total_state,
            "total_categories": total_categories,
            "total_notifications_sent": total_notifications,
            "total_applications": total_applications,
            "active_users_today": active_today,
        }

    async def get_popular_schemes(self, limit: int = 10) -> list[dict]:
        """Get most popular schemes by view count."""
        result = await self.db.execute(
            select(Scheme)
            .where(Scheme.is_active == True)
            .order_by(Scheme.view_count.desc())
            .limit(limit)
        )
        schemes = result.scalars().all()

        return [
            {
                "scheme_name": s.scheme_name,
                "slug": s.slug,
                "view_count": s.view_count,
                "application_count": s.application_count,
                "category": s.scheme_category,
            }
            for s in schemes
        ]

    async def get_category_distribution(self) -> list[dict]:
        """Get scheme distribution by category."""
        result = await self.db.execute(
            select(Scheme.scheme_category, func.count(Scheme.id))
            .where(Scheme.is_active == True)
            .group_by(Scheme.scheme_category)
            .order_by(func.count(Scheme.id).desc())
        )
        rows = result.all()
        total = sum(r[1] for r in rows)

        categories = []
        for cat, count in rows:
            if cat:
                for sub_cat in cat.split(","):
                    sub_cat = sub_cat.strip()
                    if sub_cat:
                        existing = next((c for c in categories if c["category"] == sub_cat), None)
                        if existing:
                            existing["count"] += count
                        else:
                            categories.append({
                                "category": sub_cat,
                                "count": count,
                                "percentage": round((count / max(total, 1)) * 100, 1),
                            })

        categories.sort(key=lambda x: x["count"], reverse=True)
        # Recalculate percentages
        cat_total = sum(c["count"] for c in categories)
        for c in categories:
            c["percentage"] = round((c["count"] / max(cat_total, 1)) * 100, 1)

        return categories[:15]

    async def get_state_usage(self) -> list[dict]:
        """Get user distribution by state."""
        result = await self.db.execute(
            select(User.state, func.count(User.id))
            .where(User.state.isnot(None))
            .group_by(User.state)
            .order_by(func.count(User.id).desc())
        )
        rows = result.all()

        return [
            {
                "state": state or "Unknown",
                "user_count": count,
                "scheme_count": 0,  # Will be enriched later
            }
            for state, count in rows
        ]

    async def get_eligibility_distribution(self) -> dict:
        """Get distribution of eligibility check results."""
        result = await self.db.execute(
            select(
                ApplicationTracker.eligibility_status,
                func.count(ApplicationTracker.id),
            )
            .where(ApplicationTracker.eligibility_status.isnot(None))
            .group_by(ApplicationTracker.eligibility_status)
        )
        rows = result.all()

        return {
            status or "unknown": count
            for status, count in rows
        } or {"eligible": 0, "partially_eligible": 0, "not_eligible": 0}

    async def get_monthly_signups(self, months: int = 12) -> list[dict]:
        """Get monthly user signup data."""
        data = []
        now = datetime.now(timezone.utc)

        for i in range(months - 1, -1, -1):
            month_start = (now - timedelta(days=30 * i)).replace(day=1, hour=0, minute=0, second=0)
            if i > 0:
                month_end = (now - timedelta(days=30 * (i - 1))).replace(day=1, hour=0, minute=0, second=0)
            else:
                month_end = now

            result = await self.db.execute(
                select(func.count(User.id)).where(
                    User.created_at >= month_start,
                    User.created_at < month_end,
                )
            )
            count = result.scalar() or 0

            data.append({
                "month": month_start.strftime("%b %Y"),
                "count": count,
            })

        return data

    async def get_notification_stats(self) -> dict:
        """Get notification statistics."""
        total = await self._count(Notification)
        read_result = await self.db.execute(
            select(func.count(Notification.id)).where(Notification.is_read == True)
        )
        read = read_result.scalar() or 0

        # By type
        type_result = await self.db.execute(
            select(Notification.notification_type, func.count(Notification.id))
            .group_by(Notification.notification_type)
        )
        by_type = {t: c for t, c in type_result.all()}

        return {
            "total": total,
            "read": read,
            "unread": total - read,
            "read_rate": round((read / max(total, 1)) * 100, 1),
            "by_type": by_type,
        }

    async def get_full_dashboard(self) -> dict:
        """Get complete analytics dashboard data."""
        stats = await self.get_dashboard_stats()
        popular = await self.get_popular_schemes()
        categories = await self.get_category_distribution()
        state_usage = await self.get_state_usage()
        eligibility = await self.get_eligibility_distribution()
        monthly = await self.get_monthly_signups()
        notifications = await self.get_notification_stats()

        return {
            "stats": stats,
            "popular_schemes": popular,
            "category_distribution": categories,
            "state_usage": state_usage,
            "eligibility_distribution": eligibility,
            "monthly_signups": monthly,
            "notification_stats": notifications,
        }

    async def _count(self, model, *filters):
        """Helper to count records."""
        query = select(func.count(model.id))
        for f in filters:
            query = query.where(f)
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def track_event(
        self,
        event_type: str,
        user_id: int = None,
        scheme_id: int = None,
        event_data: dict = None,
    ):
        """Track an analytics event."""
        event = AnalyticsEvent(
            user_id=user_id,
            event_type=event_type,
            scheme_id=scheme_id,
            event_data=event_data,
        )
        self.db.add(event)
