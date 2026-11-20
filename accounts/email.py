import logging
import threading
from email.mime.image import MIMEImage
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def _send_welcome_worker(user_id, recipient):
    try:
        from django.contrib.auth.models import User
        from bookings.mpesa import format_phone_number
        user = User.objects.select_related('profile').get(pk=user_id)
        raw_phone = getattr(user, 'profile', None).phone_number if hasattr(user, 'profile') else ''
        phone_display = f"+{format_phone_number(raw_phone)}" if raw_phone else ''

        subject = f"Welcome to EventHub Campus, {user.first_name or user.username}! 🎓"
        context = {
            'user': user,
            'phone': phone_display,
            'site_url': getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000').rstrip('/'),
        }

        html_content = render_to_string('emails/welcome.html', context)
        text_content = strip_tags(html_content)

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient],
        )
        email.attach_alternative(html_content, "text/html")

        # Attach logo inline
        logo_path = settings.BASE_DIR / 'static' / 'images' / 'email_logo.png'
        if not logo_path.exists():
            logo_path = settings.BASE_DIR / 'static' / 'images' / 'logo.png'

        if logo_path.exists():
            try:
                with open(logo_path, 'rb') as f:
                    logo_bytes = f.read()
                logo_mime = MIMEImage(logo_bytes, _subtype='png')
                logo_mime.add_header('Content-ID', '<brand_logo>')
                logo_mime.add_header('Content-Disposition', 'inline', filename='eventhub_logo.png')
                email.attach(logo_mime)
            except Exception as e:
                logger.warning(f"Could not attach inline logo in welcome email: {e}")

        email.send(fail_silently=False)
        logger.info(f"Welcome email successfully sent to {recipient} (User {user_id})")
    except Exception as e:
        logger.error(f"[EMAIL ERROR] Failed to send welcome email to {recipient}: {e}", exc_info=True)


def send_welcome_email(user):
    """
    Dispatches account creation welcome email in a background thread.
    """
    if not user.email:
        return False

    thread = threading.Thread(
        target=_send_welcome_worker,
        args=(user.id, user.email),
        daemon=True
    )
    thread.start()
    return True
