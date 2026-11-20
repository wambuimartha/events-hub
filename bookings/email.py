import io
import logging
import threading
import qrcode
from email.mime.image import MIMEImage
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def _send_ticket_email_worker(booking_id, recipient):
    """
    Background worker thread function to render template, generate inline QR pass,
    attach the official campus brand logo, and dispatch SMTP email without delaying the HTTP response.
    """
    try:
        from bookings.models import Booking
        booking = Booking.objects.select_related('ticket_type__event', 'user').get(pk=booking_id)
        event = booking.ticket_type.event
        ticket = booking.ticket_type
        subject = f"Your Admission Pass: {event.title} [#{str(booking.code)[:8]}]"

        context = {
            'booking': booking,
            'event': event,
            'ticket': ticket,
            'user': booking.user,
            'site_url': getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000').rstrip('/'),
        }

        # Render HTML and plain text alternative
        html_content = render_to_string('emails/ticket_confirmation.html', context)
        text_content = strip_tags(html_content)

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient],
        )
        email.attach_alternative(html_content, "text/html")

        # 1. Attach Official Brand Logo Inline (cid:brand_logo)
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
                logger.warning(f"Could not attach inline logo: {e}")

        # 2. Generate QR Code Pass and attach Inline (cid:ticket_qr)
        try:
            qr = qrcode.QRCode(box_size=8, border=2)
            qr.add_data(str(booking.code))
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")

            buf = io.BytesIO()
            img.save(buf, format='PNG')
            qr_bytes = buf.getvalue()

            qr_mime = MIMEImage(qr_bytes, _subtype='png')
            qr_mime.add_header('Content-ID', '<ticket_qr>')
            qr_mime.add_header('Content-Disposition', 'inline', filename=f"ticket-pass-{str(booking.code)[:8]}.png")
            email.attach(qr_mime)
        except Exception as qr_err:
            logger.error(f"Failed to generate QR attachment for booking {booking.id}: {qr_err}")

        email.send(fail_silently=False)
        logger.info(f"Ticket confirmation email sent to {recipient} for booking {booking.id}")
    except Exception as e:
        logger.error(f"Failed to dispatch ticket confirmation email for booking {booking_id}: {e}")


def send_ticket_confirmation_email(booking):
    """
    Spawns background email dispatch so the booking UI completes instantly and reliably.
    """
    recipient = booking.attendee_email or booking.user.email
    if not recipient:
        logger.warning(f"Booking {booking.id} user '{booking.user.username}' has no email address. Skipping email.")
        return False

    thread = threading.Thread(
        target=_send_ticket_email_worker,
        args=(booking.id, recipient),
        daemon=True
    )
    thread.start()
    return True


