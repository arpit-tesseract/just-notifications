import logging
from typing import List, Dict, Any, Optional
from django.core.mail import EmailMultiAlternatives
from django.conf import settings

logger = logging.getLogger(__name__)


class EmailServiceError(Exception):
    """Base exception for all Email service errors."""
    pass


class EmailService:
    """
    Service responsible for constructing and sending system emails.
    Supports text/HTML alternatives and attachment files.
    """

    @classmethod
    def send_email(
        cls,
        recipient_email: str,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        from_email: Optional[str] = None
    ) -> bool:
        """
        Sends an email utilizing Django's core mail engine.

        Args:
            recipient_email (str): Target email address.
            subject (str): The email subject.
            body_text (str): Plain-text fallback email body.
            body_html (Optional[str]): HTML alternative body.
            attachments (Optional[List[Dict[str, Any]]]): List of file objects:
                [{"name": "file.pdf", "content": b'...', "mime": "application/pdf"}]
            from_email (Optional[str]): Sender email (defaults to settings.DEFAULT_FROM_EMAIL).

        Returns:
            bool: True if sent successfully, False otherwise.

        Raises:
            EmailServiceError: If drafting or SMTP processing encounters errors.
        """
        if not recipient_email:
            raise EmailServiceError("Recipient email address is required.")
        if not subject:
            raise EmailServiceError("Email subject is required.")
        if not body_text:
            raise EmailServiceError("Plain-text body is required.")

        sender = from_email or getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@shashan.com')

        try:
            email = EmailMultiAlternatives(
                subject=subject,
                body=body_text,
                from_email=sender,
                to=[recipient_email]
            )

            if body_html:
                email.attach_alternative(body_html, "text/html")

            if attachments:
                for attachment in attachments:
                    name = attachment.get('name')
                    content = attachment.get('content')
                    mime = attachment.get('mime')
                    if name and content:
                        email.attach(name, content, mime)

            # Send action (returns 1 on success)
            result = email.send()
            
            if result:
                logger.info(f"Email successfully sent to {recipient_email} (Subject: '{subject}')")
                return True
            else:
                logger.error(f"SMTP returned zero sent messages for recipient {recipient_email}")
                return False

        except Exception as e:
            logger.error(f"Failed sending email to {recipient_email}: {str(e)}")
            raise EmailServiceError(f"Email SMTP dispatch error: {str(e)}") from e
