import logging

from celery import shared_task
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_account_email(self, recipient_email, subject, message):
    try:
        send_mail(subject=subject, message=message, from_email=None, recipient_list=[recipient_email], fail_silently=False)
    except Exception as exc:
        logger.warning("Account email to %s failed (attempt %s): %s", recipient_email, self.request.retries, exc)
        raise self.retry(exc=exc)
