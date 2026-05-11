"""
Notification service — system-triggered automated notifications.
Reminders are sent by the SYSTEM, not by managers manually (mentor feedback).
Pluggable: swappable between email, SQS, internal company API.
"""
from shared.base.service import BaseService


class NotificationService(BaseService):
    """
    Sends automated system notifications.
    Concrete implementations: EmailNotification, SQSNotification, WebhookNotification.
    Use dependency injection to swap without changing calling code.
    """

    async def send_reminder(self, recipient_id: str, message: str, channel: str = "email") -> bool:
        """Send a reminder notification. Returns True on success."""
        raise NotImplementedError("Use a concrete implementation of NotificationService.")

    async def send_bulk_reminder(self, recipient_ids: list[str], message: str) -> dict:
        """Send reminder to multiple recipients. Returns {success: [], failed: []}."""
        results = {"success": [], "failed": []}
        for recipient_id in recipient_ids:
            try:
                await self.send_reminder(recipient_id, message)
                results["success"].append(recipient_id)
            except Exception:
                results["failed"].append(recipient_id)
        return results
