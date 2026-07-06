"""
Celery application for background tasks: email dispatch, scheduled reports, etc.
"""
from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "mbcu_erp",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.task_routes = {
    "app.core.celery_app.send_email_notification": {"queue": "notifications"},
}


@celery_app.task(name="app.core.celery_app.send_email_notification")
def send_email_notification(to_email: str, subject: str, body: str):
    """
    Placeholder email sender. Wire this up to an SMTP provider (e.g. SendGrid,
    Mailgun, or Tanzanian SMS gateway) in production.
    """
    print(f"[EMAIL] To: {to_email} | Subject: {subject}\n{body}")
    return {"to": to_email, "subject": subject, "sent": True}
