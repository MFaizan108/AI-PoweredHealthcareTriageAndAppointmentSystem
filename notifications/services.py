import logging

from .models import Notification
from .tasks import send_notification_email

logger = logging.getLogger(__name__)


def notify(recipient, notification_type, title, message, send_email=True):
    """Create an in-app notification and hand email delivery off to Celery. Never raises."""
    notification = Notification.objects.create(
        recipient=recipient,
        notification_type=notification_type,
        title=title,
        message=message,
    )

    if send_email and recipient.email:
        try:
            send_notification_email.delay(recipient.email, title, message)
        except Exception:
            logger.exception("Failed to queue notification email to %s", recipient.email)

    return notification
