"""
Rule Change Detection using Myers Diff Algorithm.

Detects added, removed, and modified rules when scheme data is updated.
Generates impact summaries and identifies affected users.
"""

import difflib
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from app.models.scheme import Scheme, SchemeVersion
from app.models.user import User
from app.models.notification import Notification


class RuleChangeDetector:
    """Detects changes in scheme rules using Myers diff algorithm."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect_changes(
        self,
        scheme_id: int,
        new_eligibility: Optional[str] = None,
        new_benefits: Optional[str] = None,
        new_documents: Optional[str] = None,
        new_details: Optional[str] = None,
        admin_user_id: Optional[int] = None,
    ) -> dict:
        """
        Compare new scheme data with current version.
        Returns detailed diff and impact summary.
        """
        result = await self.db.execute(select(Scheme).where(Scheme.id == scheme_id))
        scheme = result.scalar_one_or_none()
        if not scheme:
            raise ValueError("Scheme not found")

        changes = {}
        all_diffs = {}

        # Compare each field
        field_comparisons = [
            ("eligibility", scheme.eligibility, new_eligibility),
            ("benefits", scheme.benefits, new_benefits),
            ("documents_required", scheme.documents_required, new_documents),
            ("details", scheme.details, new_details),
        ]

        for field_name, old_value, new_value in field_comparisons:
            if new_value is not None and old_value != new_value:
                diff = self._myers_diff(old_value or "", new_value)
                changes[field_name] = {
                    "old": old_value,
                    "new": new_value,
                    "diff": diff,
                }
                all_diffs[field_name] = diff

        if not changes:
            return {"changed": False, "changes": {}, "impact": None}

        # Create version snapshot
        version = SchemeVersion(
            scheme_id=scheme.id,
            version_number=scheme.version + 1,
            eligibility_snapshot=scheme.eligibility,
            benefits_snapshot=scheme.benefits,
            documents_snapshot=scheme.documents_required,
            details_snapshot=scheme.details,
            change_summary=self._generate_summary(changes),
            changed_fields=list(changes.keys()),
            diff_data=all_diffs,
            created_by=admin_user_id,
        )
        self.db.add(version)

        # Update scheme
        if new_eligibility is not None:
            scheme.eligibility = new_eligibility
        if new_benefits is not None:
            scheme.benefits = new_benefits
        if new_documents is not None:
            scheme.documents_required = new_documents
        if new_details is not None:
            scheme.details = new_details
        scheme.version += 1

        # Generate impact summary
        impact = self._analyze_impact(changes)

        # Find and notify affected users
        affected_count = await self._notify_affected_users(scheme, changes, impact)

        logger.info(
            f"Rule change detected for scheme {scheme_id}: "
            f"{len(changes)} field(s) changed, {affected_count} user(s) affected"
        )

        return {
            "changed": True,
            "scheme_id": scheme.id,
            "scheme_name": scheme.scheme_name,
            "new_version": scheme.version,
            "changes": {
                k: {
                    "added_lines": v["diff"]["added"],
                    "removed_lines": v["diff"]["removed"],
                    "summary": v["diff"]["summary"],
                }
                for k, v in changes.items()
            },
            "impact": impact,
            "affected_users": affected_count,
        }

    def _myers_diff(self, old_text: str, new_text: str) -> dict:
        """
        Apply Myers diff algorithm to find changes between old and new text.
        Uses Python's difflib which implements a variant of the Myers algorithm.
        """
        old_lines = old_text.splitlines() if old_text else []
        new_lines = new_text.splitlines() if new_text else []

        differ = difflib.unified_diff(
            old_lines, new_lines,
            fromfile="previous_version",
            tofile="current_version",
            lineterm="",
        )

        added = []
        removed = []
        modified = []
        diff_lines = list(differ)

        for line in diff_lines:
            if line.startswith("+") and not line.startswith("+++"):
                added.append(line[1:].strip())
            elif line.startswith("-") and not line.startswith("---"):
                removed.append(line[1:].strip())

        # Detect modifications (similar lines that changed slightly)
        matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "replace":
                for old_line, new_line in zip(old_lines[i1:i2], new_lines[j1:j2]):
                    modified.append({
                        "old": old_line.strip(),
                        "new": new_line.strip(),
                        "similarity": difflib.SequenceMatcher(
                            None, old_line, new_line
                        ).ratio(),
                    })

        summary_parts = []
        if added:
            summary_parts.append(f"{len(added)} rule(s) added")
        if removed:
            summary_parts.append(f"{len(removed)} rule(s) removed")
        if modified:
            summary_parts.append(f"{len(modified)} rule(s) modified")

        return {
            "added": added,
            "removed": removed,
            "modified": modified,
            "summary": "; ".join(summary_parts) if summary_parts else "No changes",
            "diff_text": "\n".join(diff_lines),
        }

    def _generate_summary(self, changes: dict) -> str:
        """Generate a human-readable summary of all changes."""
        parts = []
        for field, data in changes.items():
            diff = data["diff"]
            field_display = field.replace("_", " ").title()
            parts.append(f"{field_display}: {diff['summary']}")
        return " | ".join(parts)

    def _analyze_impact(self, changes: dict) -> dict:
        """Analyze the impact of changes on users."""
        impact = {
            "severity": "low",
            "categories": [],
            "description": "",
        }

        descriptions = []

        if "eligibility" in changes:
            diff = changes["eligibility"]["diff"]
            impact["categories"].append("eligibility_criteria")

            # Check for income changes
            for line in diff["added"] + [m["new"] for m in diff["modified"]]:
                if any(kw in line.lower() for kw in ["income", "₹", "rs"]):
                    impact["categories"].append("income_limit_changed")
                    impact["severity"] = "high"
                    descriptions.append("Income eligibility criteria changed")

                if any(kw in line.lower() for kw in ["age", "years"]):
                    impact["categories"].append("age_limit_changed")
                    impact["severity"] = "high"
                    descriptions.append("Age eligibility criteria changed")

                if any(kw in line.lower() for kw in ["deadline", "last date", "apply before"]):
                    impact["categories"].append("deadline_changed")
                    descriptions.append("Application deadline changed")

        if "benefits" in changes:
            impact["categories"].append("benefits_updated")
            descriptions.append("Scheme benefits have been updated")

        if "documents_required" in changes:
            impact["categories"].append("documents_changed")
            descriptions.append("Required documents list changed")
            diff = changes["documents_required"]["diff"]
            if diff["added"]:
                impact["severity"] = "high"
                descriptions.append("New documents are now required")

        impact["description"] = ". ".join(descriptions) if descriptions else "Minor updates"
        return impact

    async def _notify_affected_users(
        self,
        scheme: Scheme,
        changes: dict,
        impact: dict,
    ) -> int:
        """Create notifications for users affected by scheme changes."""
        from app.models.notification import SavedScheme as SavedSchemeModel

        # Find users who saved this scheme
        result = await self.db.execute(
            select(SavedSchemeModel).where(
                SavedSchemeModel.scheme_id == scheme.id,
                SavedSchemeModel.notify_on_changes == True,
            )
        )
        saved = result.scalars().all()

        count = 0
        for saved_scheme in saved:
            notification = Notification(
                user_id=saved_scheme.user_id,
                title=f"Scheme Updated: {scheme.scheme_name}",
                message=impact["description"],
                notification_type="rule_change",
                channel="in_app",
                priority="high" if impact["severity"] == "high" else "normal",
                scheme_id=scheme.id,
                scheme_name=scheme.scheme_name,
                change_details={
                    "changed_fields": list(changes.keys()),
                    "impact": impact,
                },
            )
            self.db.add(notification)
            count += 1

        return count


    async def get_version_history(self, scheme_id: int) -> list[dict]:
        """Get version history for a scheme."""
        result = await self.db.execute(
            select(SchemeVersion)
            .where(SchemeVersion.scheme_id == scheme_id)
            .order_by(SchemeVersion.version_number.desc())
        )
        versions = result.scalars().all()

        return [
            {
                "version": v.version_number,
                "change_summary": v.change_summary,
                "changed_fields": v.changed_fields,
                "created_at": v.created_at.isoformat() if v.created_at else None,
            }
            for v in versions
        ]
