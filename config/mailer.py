import os
import base64
import logging
import requests
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def dispatch_email(subject, recipient, html_content, qr_bytes=None, logo_bytes=None):
    """
    Unified email dispatcher supporting:
    1. Google Apps Script Web App (HTTPS Port 443 — 100% Free, Native Gmail)
    2. Brevo REST API (HTTPS port 443)
    3. Resend REST API (HTTPS port 443)
    4. Django Standard SMTP (ports 587/465 — localhost & paid cloud tiers)
    """
    gmail_webapp_url = (
        getattr(settings, 'GMAIL_WEBAPP_URL', '') or
        os.environ.get('GMAIL_WEBAPP_URL', '')
    ).strip()
    brevo_api_key = (
        getattr(settings, 'BREVO_API_KEY', '') or
        os.environ.get('BREVO_API_KEY', '')
    ).strip()
    resend_api_key = (
        getattr(settings, 'RESEND_API_KEY', '') or
        os.environ.get('RESEND_API_KEY', '')
    ).strip()

    sender_email = getattr(settings, 'EMAIL_HOST_USER', 'wammarz15@gmail.com')
    sender_name = "EventHub Campus"

    print(
        f"[MAILER] Target: {recipient} | Subject: '{subject[:30]}...' | "
        f"GMAIL_WEBAPP_URL: {'CONFIGURED' if gmail_webapp_url else 'NOT_SET'} | "
        f"BREVO: {'SET' if brevo_api_key else 'NO'} | RESEND: {'SET' if resend_api_key else 'NO'}",
        flush=True
    )

    # =========================================================================
    # OPTION 0: Google Apps Script Web App (HTTPS Port 443 — 100% Free, Native Gmail)
    # =========================================================================
    if gmail_webapp_url:
        try:
            print(f"[GMAIL WEBAPP] Dispatching HTTPS request to Google Web App...", flush=True)
            payload = {
                "to": recipient,
                "subject": subject,
                "html": html_content,
            }
            attachments = []
            if qr_bytes:
                attachments.append({
                    "name": "ticket-pass-qr.png",
                    "content": base64.b64encode(qr_bytes).decode('utf-8'),
                    "mimeType": "image/png"
                })
            if logo_bytes:
                attachments.append({
                    "name": "eventhub-logo.png",
                    "content": base64.b64encode(logo_bytes).decode('utf-8'),
                    "mimeType": "image/png"
                })
            if attachments:
                payload["attachments"] = attachments

            resp = requests.post(
                gmail_webapp_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=25,
                allow_redirects=True
            )
            print(f"[GMAIL WEBAPP RESPONSE] HTTP {resp.status_code} | Body: {resp.text[:160]}", flush=True)

            if "success" in resp.text.lower() or resp.status_code in (200, 302):
                print(f"[GMAIL WEBAPP SUCCESS] Ticket email delivered to {recipient}", flush=True)
                return True
            else:
                print(f"[GMAIL WEBAPP WARNING] Unexpected response: {resp.status_code} - {resp.text[:120]}", flush=True)
        except Exception as e:
            print(f"[GMAIL WEBAPP EXCEPTION] Error posting to Web App: {e}", flush=True)

    # =========================================================================
    # OPTION 1: Brevo HTTPS REST API (Port 443)
    # =========================================================================
    if brevo_api_key:
        try:
            url = "https://api.brevo.com/v3/smtp/email"
            headers = {
                "accept": "application/json",
                "api-key": brevo_api_key,
                "content-type": "application/json"
            }
            payload = {
                "sender": {"name": sender_name, "email": sender_email},
                "to": [{"email": recipient}],
                "subject": subject,
                "htmlContent": html_content,
            }
            attachments = []
            if qr_bytes:
                attachments.append({
                    "name": "campus-ticket-qr.png",
                    "content": base64.b64encode(qr_bytes).decode('utf-8')
                })
            if logo_bytes:
                attachments.append({
                    "name": "eventhub-logo.png",
                    "content": base64.b64encode(logo_bytes).decode('utf-8')
                })
            if attachments:
                payload["attachment"] = attachments

            resp = requests.post(url, json=payload, headers=headers, timeout=10)
            if resp.status_code in (200, 201, 202):
                print(f"[BREVO HTTPS SUCCESS] Email delivered to {recipient}", flush=True)
                return True
            else:
                print(f"[BREVO HTTPS ERROR] Status {resp.status_code}: {resp.text}", flush=True)
        except Exception as e:
            print(f"[BREVO EXCEPTION] {e}", flush=True)

    # =========================================================================
    # OPTION 2: Resend HTTPS REST API (Port 443)
    # =========================================================================
    if resend_api_key:
        try:
            url = "https://api.resend.com/emails"
            headers = {
                "Authorization": f"Bearer {resend_api_key}",
                "Content-Type": "application/json"
            }
            from_addr = f"{sender_name} <onboarding@resend.dev>"
            payload = {
                "from": from_addr,
                "to": [recipient],
                "subject": subject,
                "html": html_content,
            }
            attachments = []
            if qr_bytes:
                attachments.append({
                    "filename": "campus-ticket-qr.png",
                    "content": base64.b64encode(qr_bytes).decode('utf-8')
                })
            if attachments:
                payload["attachments"] = attachments

            resp = requests.post(url, json=payload, headers=headers, timeout=10)
            if resp.status_code in (200, 201, 202):
                print(f"[RESEND HTTPS SUCCESS] Email delivered to {recipient}", flush=True)
                return True
            else:
                print(f"[RESEND HTTPS ERROR] Status {resp.status_code}: {resp.text}", flush=True)
        except Exception as e:
            print(f"[RESEND EXCEPTION] {e}", flush=True)

    # =========================================================================
    # OPTION 3: Standard Django SMTP (Port 587)
    # Note: Blocked on Render Free Tier; works on localhost and paid tiers.
    # =========================================================================
    try:
        from email.mime.image import MIMEImage
        text_content = strip_tags(html_content)
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient],
        )
        email.attach_alternative(html_content, "text/html")

        if logo_bytes:
            try:
                logo_mime = MIMEImage(logo_bytes, _subtype='png')
                logo_mime.add_header('Content-ID', '<brand_logo>')
                logo_mime.add_header('Content-Disposition', 'inline', filename='eventhub_logo.png')
                email.attach(logo_mime)
            except Exception:
                pass

        if qr_bytes:
            try:
                qr_mime = MIMEImage(qr_bytes, _subtype='png')
                qr_mime.add_header('Content-ID', '<ticket_qr>')
                qr_mime.add_header('Content-Disposition', 'inline', filename='ticket-qr.png')
                email.attach(qr_mime)
            except Exception:
                pass

        email.send(fail_silently=False)
        print(f"[SMTP SUCCESS] Email delivered to {recipient}", flush=True)
        return True
    except Exception as smtp_err:
        err_msg = str(smtp_err)
        print(f"[SMTP FAILED] {err_msg}", flush=True)
        if "network is unreachable" in err_msg.lower() or "timed out" in err_msg.lower() or "101" in err_msg or "110" in err_msg:
            print(
                "[RENDER FREE TIER LIMITATION] Render actively blocks outbound SMTP (port 587). "
                "Ensure GMAIL_WEBAPP_URL is saved in Render Dashboard -> Environment to route through Google Apps Script over HTTPS.",
                flush=True
            )
        return False
