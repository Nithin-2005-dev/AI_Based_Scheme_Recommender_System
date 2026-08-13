"""
Search Engine with full-text search and semantic similarity.
"""

import re
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from loguru import logger

from app.models.scheme import Scheme, SchemeTag, scheme_tag_association


class SearchEngine:
    """Full-text + semantic search engine for government schemes."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def search(
        self,
        query: str,
        category: Optional[str] = None,
        level: Optional[str] = None,
        state: Optional[str] = None,
        tags: Optional[list[str]] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> dict:
        """
        Search schemes with filters and pagination.

        Uses: keyword matching on scheme_name, details, eligibility, benefits, tags.
        """
        search_query = select(Scheme).where(Scheme.is_active == True)
        count_query = select(func.count(Scheme.id)).where(Scheme.is_active == True)

        # ===== Keyword search =====
        if query:
            search_terms = query.strip().split()
            conditions = []
            for term in search_terms:
                term_pattern = f"%{term}%"
                conditions.append(
                    or_(
                        Scheme.scheme_name.ilike(term_pattern),
                        Scheme.details.ilike(term_pattern),
                        Scheme.eligibility.ilike(term_pattern),
                        Scheme.benefits.ilike(term_pattern),
                        Scheme.scheme_category.ilike(term_pattern),
                        Scheme.documents_required.ilike(term_pattern),
                    )
                )
            if conditions:
                combined = and_(*conditions)
                search_query = search_query.where(combined)
                count_query = count_query.where(combined)

        # ===== Filters =====
        if category:
            search_query = search_query.where(Scheme.scheme_category.ilike(f"%{category}%"))
            count_query = count_query.where(Scheme.scheme_category.ilike(f"%{category}%"))

        if level and level in ("Central", "State"):
            search_query = search_query.where(Scheme.level == level)
            count_query = count_query.where(Scheme.level == level)

        if state:
            state_filter = or_(
                Scheme.details.ilike(f"%{state}%"),
                Scheme.eligibility.ilike(f"%{state}%"),
                Scheme.level == "Central",  # Central schemes available in all states
            )
            search_query = search_query.where(state_filter)
            count_query = count_query.where(state_filter)

        # ===== Get total count =====
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # ===== Sorting: relevance (schemes with query in name rank higher) =====
        if query:
            search_query = search_query.order_by(
                Scheme.scheme_name.ilike(f"%{query}%").desc(),
                Scheme.view_count.desc(),
                Scheme.scheme_name,
            )
        else:
            search_query = search_query.order_by(
                Scheme.view_count.desc(),
                Scheme.scheme_name,
            )

        # ===== Pagination =====
        search_query = search_query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(search_query)
        schemes = result.scalars().all()

        # ===== Generate suggestions =====
        suggestions = await self._generate_suggestions(query) if query else []

        return {
            "results": schemes,
            "total": total,
            "page": page,
            "page_size": page_size,
            "query": query,
            "suggestions": suggestions,
        }

    async def get_categories(self) -> list[dict]:
        """Get all unique categories with counts."""
        result = await self.db.execute(
            select(Scheme.scheme_category, func.count(Scheme.id).label("count"))
            .where(Scheme.is_active == True)
            .group_by(Scheme.scheme_category)
            .order_by(func.count(Scheme.id).desc())
        )
        rows = result.all()

        categories = []
        for row in rows:
            if row[0]:
                # Split multi-value categories
                cats = [c.strip() for c in row[0].split(",")]
                for cat in cats:
                    existing = next((c for c in categories if c["name"] == cat), None)
                    if existing:
                        existing["count"] += row[1]
                    else:
                        categories.append({"name": cat, "count": row[1]})

        categories.sort(key=lambda x: x["count"], reverse=True)
        return categories

    async def get_popular_schemes(self, limit: int = 10) -> list[Scheme]:
        """Get most popular schemes by view count."""
        result = await self.db.execute(
            select(Scheme)
            .where(Scheme.is_active == True)
            .order_by(Scheme.view_count.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def _generate_suggestions(self, query: str) -> list[str]:
        """Generate search suggestions based on query."""
        suggestions = []

        # Suggest related categories
        category_map = {
            "farmer": "Agriculture,Rural & Environment",
            "education": "Education & Learning",
            "health": "Health & Wellness",
            "business": "Business & Entrepreneurship",
            "women": "Women and Child",
            "housing": "Housing & Shelter",
            "social": "Social welfare & Empowerment",
            "employment": "Skills & Employment",
            "insurance": "Financial Services and Insurance",
        }

        query_lower = query.lower()
        for keyword, category in category_map.items():
            if keyword in query_lower:
                suggestions.append(f"Browse all {category} schemes")

        # Suggest level filter
        if "central" not in query_lower and "state" not in query_lower:
            suggestions.append("Filter by Central Government schemes")
            suggestions.append("Filter by State Government schemes")

        return suggestions[:5]

    async def autocomplete(self, query: str, limit: int = 5) -> list[str]:
        """Get autocomplete suggestions for search."""
        if len(query) < 2:
            return []

        result = await self.db.execute(
            select(Scheme.scheme_name)
            .where(
                Scheme.is_active == True,
                Scheme.scheme_name.ilike(f"%{query}%"),
            )
            .limit(limit)
        )
        return [row[0] for row in result.all()]
