"""
Notification service -- system-triggered automated notifications.
Reminders are sent by the SYSTEM, not by managers manually (mentor feedback).
Pluggable: swappable between email, SQS, internal company API.
"""
from abc import abstractmethod
from dataclasses import dataclass
from shared.base.service import BaseService


@dataclass
class Notification:
    """
    Immutable notification payload.
    Built by _build_notification; dispatched by send_reminder.
    Separating construction from dispatch satisfies SRP.
    """
    recipient_id: str
    message: str
    channel: str = "email"


class NotificationService(BaseService):
    """
    Sends automated system notifications.
    Concrete implementations: EmailNotification, SQSNotification, WebhookNotification.
    Use dependency injection to swap without changing calling code.
    """

    @abstractmethod
    async def send_reminder(self, notification: Notification) -> bool:
        """
        Dispatch a pre-built notification. Returns True on success.
        Every concrete subclass must implement this -- enforced at instantiation.
        """
        ...

    def _build_notification(
        self, recipient_id: str, message: str, channel: str = "email"
    ) -> Notification:
        """
        SRP: owns notification construction only.
        Called before send_reminder so building and sending stay independent.
        """
        return Notification(recipient_id=recipient_id, message=message, channel=channel)

    async def send_bulk_reminder(
        self, recipient_ids: list[str], message: str, channel: str = "email"
    ) -> dict:
        """
        Send reminder to multiple recipients.
        Returns {success: [ids], failed: [ids]}.
        Delegates construction to _build_notification and dispatch to send_reminder.
        """
        results: dict[str, list[str]] = {"success": [], "failed": []}
        for recipient_id in recipient_ids:
            notification = self._build_notification(recipient_id, message, channel)
            try:
                await self.send_reminder(notification)
                results["success"].append(recipient_id)
            except Exception:
                results["failed"].append(recipient_id)
        return results
