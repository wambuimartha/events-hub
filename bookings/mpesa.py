import base64
import json
import logging
from datetime import datetime
from decouple import config
import requests
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)

# Safaricom Daraja Configuration (defaulted to standard Safaricom Sandbox credentials)
MPESA_ENVIRONMENT = config('MPESA_ENVIRONMENT', default='sandbox').lower()
MPESA_CONSUMER_KEY = config('MPESA_CONSUMER_KEY', default='wQe8WBnXiP8kK4NTqfTCTbeqwCpDHNZkRjoQBBVMABf8u3oq')
MPESA_CONSUMER_SECRET = config('MPESA_CONSUMER_SECRET', default='8uUArjjA3OLiZtHIjdWHWaAmFlvmi3tCWafAsoYG9qWiizXrY7iht6weuwlo4y1G')
MPESA_SHORTCODE = config('MPESA_SHORTCODE', default='174379')
MPESA_PASSKEY = config('MPESA_PASSKEY', default='bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919')

DEFAULT_SITE_URL = config('SITE_URL', default='https://events-hub-rygr.onrender.com').rstrip('/')
MPESA_CALLBACK_URL = config('MPESA_CALLBACK_URL', default=f"{DEFAULT_SITE_URL}/bookings/mpesa/callback/")

if MPESA_ENVIRONMENT == 'production':
    BASE_URL = 'https://api.safaricom.co.ke'
else:
    BASE_URL = 'https://sandbox.safaricom.co.ke'


def format_phone_number(phone: str) -> str:
    """Format Kenyan phone number into 254XXXXXXXXX standard format."""
    phone = str(phone).strip().replace(' ', '').replace('-', '')
    if phone.startswith('+'):
        phone = phone[1:]
    if phone.startswith('0'):
        phone = '254' + phone[1:]
    elif phone.startswith('7') or phone.startswith('1'):
        phone = '254' + phone
    return phone


def get_mpesa_access_token():
    """Generate OAuth access token from Safaricom Daraja API."""
    url = f"{BASE_URL}/oauth/v1/generate?grant_type=client_credentials"
    response = requests.get(
        url,
        auth=HTTPBasicAuth(MPESA_CONSUMER_KEY, MPESA_CONSUMER_SECRET),
        timeout=10
    )
    response.raise_for_status()
    data = response.json()
    return data.get('access_token')


def generate_mpesa_password():
    """Generate timestamp and Base64 password for Lipa na M-Pesa Online (STK Push)."""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    data_to_encode = f"{MPESA_SHORTCODE}{MPESA_PASSKEY}{timestamp}"
    password = base64.b64encode(data_to_encode.encode('utf-8')).decode('utf-8')
    return timestamp, password


def initiate_stk_push(phone_number: str, amount: int, account_reference: str, transaction_desc: str = 'EventHub Ticket'):
    """Initiate Lipa na M-Pesa Online STK Push request."""
    try:
        formatted_phone = format_phone_number(phone_number)
        token = get_mpesa_access_token()
        timestamp, password = generate_mpesa_password()

        url = f"{BASE_URL}/mpesa/stkpush/v1/processrequest"
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        }

        payload = {
            "BusinessShortCode": MPESA_SHORTCODE,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(amount),
            "PartyA": formatted_phone,
            "PartyB": MPESA_SHORTCODE,
            "PhoneNumber": formatted_phone,
            "CallBackURL": MPESA_CALLBACK_URL,
            "AccountReference": str(account_reference)[:12],
            "TransactionDesc": str(transaction_desc)[:13],
        }

        response = requests.post(url, json=payload, headers=headers, timeout=10)
        result = response.json()
        logger.info(f"M-Pesa STK Push response: {result}")
        return {
            'success': response.status_code == 200 and result.get('ResponseCode') == '0',
            'data': result,
            'status_code': response.status_code
        }
    except Exception as e:
        logger.error(f"Error initiating STK push: {e}")
        return {
            'success': False,
            'error': str(e)
        }
