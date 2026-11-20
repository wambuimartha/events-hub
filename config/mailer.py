import os
import base64
import logging
import requests
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def find_gmail_webapp_url():
    """
    Bulletproof auto-discovery for Google Apps Script Web App URL.
    Scans settings, standard environment keys, and any environment variable
    containing 'script.google.com' so no typo can ever prevent it from being found.
    """
    # 1. Check settings
    val = getattr(settings, 'GMAIL_WEBAPP_URL', '')
    if val and 'script.google.com' in str(val):
        url = str(val).strip().strip('"').strip("'")
        return _normalize_script_url(url)

    # 2. Check standard environment variable names
    candidates = [
        'GMAIL_WEBAPP_URL',
        'GMAIL_WEB_APP_URL',
        'GMAIL_URL',
        'WEBAPP_URL',
        'SCRIPT_URL',
        'GOOGLE_SCRIPT_URL',
        'GOOGLE_APPS_SCRIPT_URL',
        'GMAIL_SCRIPT_URL',
    ]
    for key in candidates:
        v = os.environ.get(key, '').strip().strip('"').strip("'")
        if v and 'script.google.com' in v:
            print(f"[MAILER AUTO-DETECT] Found Web App URL in '{key}'", flush=True)
            return _normalize_script_url(v)

    # 3. Dynamic scan: check ALL environment variables for 'script.google.com'
    for k, v in os.environ.items():
        if 'script.google.com' in str(v):
            cleaned = str(v).strip().strip('"').strip("'")
            print(f"[MAILER AUTO-DETECT] Found Web App URL in env var '{k}'", flush=True)
            return _normalize_script_url(cleaned)

    return ''


def _normalize_script_url(url):
    """Ensure the Google Apps Script Web App URL terminates in /exec."""
    if '/edit' in url:
        url = url.split('/edit')[0] + '/exec'
    elif not url.endswith('/exec'):
        url = url.rstrip('/') + '/exec'
    return url


def dispatch_email(subject, recipient, html_content, qr_bytes=None, logo_bytes=None):
    """
    Unified email dispatcher:
    1. Google Apps Script Web App (HTTPS port 443 — 100% Free, Native Gmail, zero port blocks)
    2. Brevo HTTPS API (Port 443)
    3. Resend HTTPS API (Port 443)
    4. Standard Django SMTP (Port 587 — localhost/paid cloud tiers)
    """
    gmail_webapp_url = find_gmail_webapp_url()
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
        f"GMAIL_WEBAPP_URL: {'FOUND' if gmail_webapp_url else 'NOT_FOUND'}",
        flush=True
    )

    # =========================================================================
    # OPTION 0: Google Apps Script Web App (HTTPS Port 443)
    # =========================================================================
    if gmail_webapp_url:
        try:
            print(f"[GMAIL WEBAPP] Dispatching HTTPS POST to: {gmail_webapp_url[:50]}...", flush=True)
            payload = {
                "to": recipient,
                "subject": subject,
                "html": html_content,
            }
            attachments = []
            inline_images = {}
            if qr_bytes:
                b64_qr = base64.b64encode(qr_bytes).decode('utf-8')
                attachments.append({
                    "name": "ticket-pass-qr.png",
                    "content": b64_qr,
                    "mimeType": "image/png"
                })
                inline_images["ticket_qr"] = {
                    "content": b64_qr,
                    "mimeType": "image/png"
                }
            if logo_bytes:
                b64_logo = base64.b64encode(logo_bytes).decode('utf-8')
                attachments.append({
                    "name": "eventhub-logo.png",
                    "content": b64_logo,
                    "mimeType": "image/png"
                })
                inline_images["brand_logo"] = {
                    "content": b64_logo,
                    "mimeType": "image/png"
                }

            payload = {
                "to": recipient,
                "subject": subject,
                "html": html_content,
                "inlineImages": inline_images,
                "attachments": attachments,
            }

            resp = requests.post(
                gmail_webapp_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30,
                allow_redirects=True
            )
            print(f"[GMAIL WEBAPP RESPONSE] HTTP {resp.status_code} | Body: {resp.text[:180]}", flush=True)

            # Check if Google returned success or redirected to execution output
            if "success" in resp.text.lower() or resp.status_code in (200, 302):
                print(f"[GMAIL WEBAPP SUCCESS] Ticket admission email delivered to {recipient}", flush=True)
                return True
            else:
                print(f"[GMAIL WEBAPP WARNING] Unexpected response: {resp.status_code} - {resp.text[:140]}", flush=True)
        except Exception as e:
            print(f"[GMAIL WEBAPP EXCEPTION] Error calling Web App: {e}", flush=True)

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
                "[RENDER FREE TIER LIMITATION] Outbound port 587 blocked. "
                "Set GMAIL_WEBAPP_URL in Render Dashboard -> Environment to route via Google Apps Script HTTPS.",
                flush=True
            )
        return False
