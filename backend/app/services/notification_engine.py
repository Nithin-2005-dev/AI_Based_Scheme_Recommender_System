"""
Notification Engine: In-app, Email, and SMS notifications.
Personalized Notification Engine + Deadline Reminder Engine.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from loguru import logger

from app.models.notification import Notification, DeadlineReminder
from app.models.scheme import Scheme
from app.models.user import User
from app.core.config import get_settings

settings = get_settings()


class NotificationEngine:
    """Handles creation and delivery of notifications."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_notification(
        self,
        user_id: int,
        title: str,
        message: str,
        notification_type: str = "system",
        channel: str = "in_app",
        priority: str = "normal",
        scheme_id: Optional[int] = None,
        scheme_name: Optional[str] = None,
        change_details: Optional[dict] = None,
    ) -> Notification:
        """Create a new notification for a user."""
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            channel=channel,
            priority=priority,
            scheme_id=scheme_id,
            scheme_name=scheme_name,
            change_details=change_details,
        )
        self.db.add(notification)
        await self.db.flush()

        # Send via appropriate channel
        if channel == "email":
            await self._send_email_notification(user_id, title, message)
        elif channel == "sms":
            await self._send_sms_notification(user_id, title, message)

        return notification

    async def create_bulk_notification(
        self,
        title: str,
        message: str,
        notification_type: str = "system",
        target_user_ids: Optional[list[int]] = None,
        scheme_id: Optional[int] = None,
        priority: str = "normal",
    ) -> int:
        """Send notification to multiple users (or all users)."""
        if target_user_ids:
            users = target_user_ids
        else:
            result = await self.db.execute(select(User.id))
            users = [row[0] for row in result.all()]

        count = 0
        for uid in users:
            notification = Notification(
                user_id=uid,
                title=title,
                message=message,
                notification_type=notification_type,
                channel="in_app",
                priority=priority,
                scheme_id=scheme_id,
            )
            self.db.add(notification)
            count += 1

        await self.db.flush()
        logger.info(f"Sent bulk notification to {count} users: {title}")
        return count

    async def get_user_notifications(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        unread_only: bool = False,
    ) -> dict:
        """Get paginated notifications for a user."""
        query = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            query = query.where(Notification.is_read == False)
        query = query.order_by(Notification.created_at.desc())

        # Count
        count_query = select(func.count(Notification.id)).where(Notification.user_id == user_id)
        if unread_only:
            count_query = count_query.where(Notification.is_read == False)
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Unread count
        unread_result = await self.db.execute(
            select(func.count(Notification.id)).where(
                Notification.user_id == user_id,
                Notification.is_read == False,
            )
        )
        unread_count = unread_result.scalar() or 0

        # Paginate
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        notifications = result.scalars().all()

        return {
            "notifications": notifications,
            "total": total,
            "unread_count": unread_count,
        }

    async def mark_as_read(self, notification_id: int, user_id: int) -> bool:
        """Mark a notification as read."""
        result = await self.db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
        )
        notification = result.scalar_one_or_none()
        if notification:
            notification.is_read = True
            notification.read_at = datetime.now(timezone.utc)
            return True
        return False

    async def mark_all_read(self, user_id: int) -> int:
        """Mark all notifications as read for a user."""
        result = await self.db.execute(
            select(Notification).where(
                Notification.user_id == user_id,
                Notification.is_read == False,
            )
        )
        notifications = result.scalars().all()
        count = 0
        for n in notifications:
            n.is_read = True
            n.read_at = datetime.now(timezone.utc)
            count += 1
        return count

    async def _send_email_notification(self, user_id: int, title: str, message: str):
        """Send email notification (if SMTP is configured)."""
        if not settings.SMTP_USERNAME:
            logger.warning("SMTP not configured, skipping email notification")
            return

        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user or not user.email:
            return

        try:
            import aiosmtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"[GovScheme AI] {title}"
            msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
            msg["To"] = user.email

            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background: #f7f7f7; padding: 30px; border-radius: 10px;">
                    <h2 style="color: #1a365d;">{title}</h2>
                    <p style="color: #333; line-height: 1.6;">{message}</p>
                    <hr style="border: 1px solid #eee;">
                    <p style="color: #888; font-size: 12px;">
                        This is an automated notification from GovScheme AI.
                        <a href="{settings.FRONTEND_URL}/notifications">View all notifications</a>
                    </p>
                </div>
            </body>
            </html>
            """
            msg.attach(MIMEText(html_content, "html"))

            await aiosmtplib.send(
                msg,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USERNAME,
                password=settings.SMTP_PASSWORD,
                use_tls=settings.SMTP_USE_TLS,
            )
            logger.info(f"Email sent to {user.email}: {title}")
        except Exception as e:
            logger.error(f"Failed to send email: {e}")

    async def _send_sms_notification(self, user_id: int, title: str, message: str):
        """Send SMS notification (if provider is configured)."""
        if not settings.TWILIO_ACCOUNT_SID and not settings.MSG91_AUTH_KEY:
            logger.warning("SMS provider not configured, skipping SMS")
            return

        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user or not user.mobile_number:
            return

        try:
            if settings.SMS_PROVIDER == "twilio" and settings.TWILIO_ACCOUNT_SID:
                import httpx
                async with httpx.AsyncClient() as client:
                    await client.post(
                        f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID}/Messages.json",
                        auth=(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN),
                        data={
                            "From": settings.TWILIO_FROM_NUMBER,
                            "To": user.mobile_number,
                            "Body": f"{title}: {message[:140]}",
                        },
                    )
                logger.info(f"SMS sent to {user.mobile_number}")
        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")


class DeadlineReminderEngine:
    """Manages deadline reminders at 30, 15, 7, 3, 1, 0 days before deadline."""

    REMINDER_DAYS = [30, 15, 7, 3, 1, 0]

    def __init__(self, db: AsyncSession):
        self.db = db
        self.notification_engine = NotificationEngine(db)

    async def setup_reminders(self, user_id: int, scheme_id: int) -> list[DeadlineReminder]:
        """Set up deadline reminders for a user-scheme pair."""
        result = await self.db.execute(select(Scheme).where(Scheme.id == scheme_id))
        scheme = result.scalar_one_or_none()
        if not scheme or not scheme.deadline:
            return []

        reminders = []
        for days in self.REMINDER_DAYS:
            reminder = DeadlineReminder(
                user_id=user_id,
                scheme_id=scheme_id,
                deadline_date=scheme.deadline,
                reminder_days_before=days,
                reminder_type="deadline",
            )
            self.db.add(reminder)
            reminders.append(reminder)

        # Also set renewal reminder if applicable
        if scheme.renewal_date:
            for days in self.REMINDER_DAYS:
                reminder = DeadlineReminder(
                    user_id=user_id,
                    scheme_id=scheme_id,
                    deadline_date=scheme.renewal_date,
                    reminder_days_before=days,
                    reminder_type="renewal",
                )
                self.db.add(reminder)
                reminders.append(reminder)

        await self.db.flush()
        return reminders

    async def check_and_send_reminders(self) -> int:
        """Check for due reminders and send notifications. Called by scheduler."""
        now = datetime.now(timezone.utc)
        sent_count = 0

        for days in self.REMINDER_DAYS:
            target_date = now + timedelta(days=days)
            target_start = target_date.replace(hour=0, minute=0, second=0)
            target_end = target_date.replace(hour=23, minute=59, second=59)

            result = await self.db.execute(
                select(DeadlineReminder).where(
                    DeadlineReminder.is_sent == False,
                    DeadlineReminder.reminder_days_before == days,
                    DeadlineReminder.deadline_date >= target_start,
                    DeadlineReminder.deadline_date <= target_end,
                )
            )
            reminders = result.scalars().all()

            for reminder in reminders:
                # Get scheme name
                scheme_result = await self.db.execute(
                    select(Scheme.scheme_name).where(Scheme.id == reminder.scheme_id)
                )
                scheme_name = scheme_result.scalar() or "Unknown Scheme"

                if days == 0:
                    title = f"⚠️ Today is the deadline for: {scheme_name}"
                    message = f"The deadline for {scheme_name} is TODAY. Apply now!"
                else:
                    reminder_type = "Renewal" if reminder.reminder_type == "renewal" else "Deadline"
                    title = f"📅 {reminder_type} Reminder: {scheme_name}"
                    message = f"{days} day(s) remaining until the {reminder_type.lower()} for {scheme_name}."

                await self.notification_engine.create_notification(
                    user_id=reminder.user_id,
                    title=title,
                    message=message,
                    notification_type="deadline",
                    priority="high" if days <= 3 else "normal",
                    scheme_id=reminder.scheme_id,
                    scheme_name=scheme_name,
                )

                reminder.is_sent = True
                reminder.sent_at = now
                sent_count += 1

        logger.info(f"Sent {sent_count} deadline reminders")
        return sent_count
