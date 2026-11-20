import io
import logging
import qrcode
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def send_ticket_confirmation_email(booking):
    """
    Sends an HTML ticket confirmation email with the ticket QR code attached as PNG.
    Gracefully catches errors so payment flow is never blocked.
    """
    recipient = booking.attendee_email or booking.user.email
    if not recipient:
        # Fallback if the user account doesn't have an email set
        logger.warning(f"Booking {booking.id} user '{booking.user.username}' has no email address. Skipping email.")
        return False

    event = booking.ticket_type.event
    ticket = booking.ticket_type
    subject = f"Your Admission Ticket: {event.title} [#{str(booking.code)[:8]}]"

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

    # Generate QR Code in memory and attach
    try:
        qr = qrcode.QRCode(box_size=8, border=2)
        qr.add_data(str(booking.code))
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buf = io.BytesIO()
        img.save(buf, format='PNG')
        qr_bytes = buf.getvalue()

        filename = f"ticket-pass-{str(booking.code)[:8]}.png"
        email.attach(filename, qr_bytes, "image/png")
    except Exception as e:
        logger.error(f"Failed to generate QR attachment for booking {booking.id}: {e}")

    try:
        email.send(fail_silently=False)
        logger.info(f"Ticket confirmation email sent to {recipient} for booking {booking.id}")
        return True
    except Exception as e:
        logger.error(f"Failed to send ticket email to {recipient}: {e}")
        return False
