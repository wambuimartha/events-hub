import io
import json
import logging
import qrcode
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.contrib import messages
from django.http import HttpResponse, JsonResponse, Http404
from events.models import TicketType
from .models import Booking
from .mpesa import initiate_stk_push, format_phone_number
from .email import send_ticket_confirmation_email

logger = logging.getLogger(__name__)


@login_required
@require_POST
def book_ticket(request, ticket_id):
    ticket = get_object_or_404(TicketType, pk=ticket_id)
    try:
        qty = int(request.POST.get('quantity', 1))
    except (ValueError, TypeError):
        messages.error(request, 'Invalid ticket quantity.')
        return redirect('event_detail', pk=ticket.event.pk)

    if qty < 1 or qty > ticket.remaining:
        messages.error(request, 'Not enough tickets available.')
        return redirect('event_detail', pk=ticket.event.pk)

    attendee_name = request.POST.get('attendee_name', '').strip() or request.user.get_full_name() or request.user.username
    attendee_email = request.POST.get('attendee_email', '').strip() or request.user.email
    phone = request.POST.get('phone_number', '').strip()

    try:
        with transaction.atomic():
            booking = Booking.objects.create(
                user=request.user,
                ticket_type=ticket,
                quantity=qty,
                total=ticket.price * qty,
                attendee_name=attendee_name,
                attendee_email=attendee_email,
                phone_number=phone,
                status='pending'
            )

            # Free Campus Event Handling (skip M-Pesa, confirm instantly)
            if booking.total == 0:
                booking.status = 'paid'
                booking.mpesa_receipt = 'CAMPUS-FREE'
                booking.save()
                send_ticket_confirmation_email(booking)
                target_email = booking.attendee_email or request.user.email
                messages.success(
                    request, 
                    f"You're officially registered for {ticket.event.title}! Your digital ticket and QR pass have been sent to {target_email}."
                )
                return redirect('my_bookings')

        return redirect('booking_checkout', booking_id=booking.id)
    except Exception as e:
        logger.error(f"Error booking ticket {ticket_id} for user {request.user.id}: {e}", exc_info=True)
        messages.error(request, "Unable to complete reservation right now. Please try again.")
        return redirect('event_detail', pk=ticket.event.pk)


@login_required
def booking_checkout(request, booking_id):
    """Tikiti / Daraja checkout page with M-Pesa STK Push."""
    booking = get_object_or_404(Booking, pk=booking_id, user=request.user)
    if booking.status == 'paid':
        messages.info(request, 'This booking has already been paid for.')
        return redirect('my_bookings')
    return render(request, 'bookings/checkout.html', {'booking': booking})


@login_required
@require_POST
def mpesa_stk_push(request, booking_id):
    """Trigger Daraja STK Push to the user's phone."""
    booking = get_object_or_404(Booking, pk=booking_id, user=request.user)
    phone = request.POST.get('phone_number', '').strip()

    if not phone:
        messages.error(request, 'Please provide an active M-Pesa phone number.')
        return redirect('booking_checkout', booking_id=booking.id)

    formatted_phone = format_phone_number(phone)
    result = initiate_stk_push(
        phone_number=formatted_phone,
        amount=int(booking.total),
        account_reference=f"TIK-{booking.id}",
        transaction_desc=f"{booking.ticket_type.event.title[:12]}"
    )

    if result.get('success'):
        data = result.get('data', {})
        checkout_request_id = data.get('CheckoutRequestID', '')
        booking.phone_number = formatted_phone
        booking.checkout_request_id = checkout_request_id
        booking.save()
        messages.success(
            request,
            f"M-Pesa STK Push sent to {formatted_phone}! Check your phone and enter your M-Pesa PIN to complete payment."
        )
    else:
        err = result.get('error') or result.get('data', {}).get('errorMessage', 'Safaricom connection issue')
        messages.warning(
            request,
            f"STK Push notice: {err}. If running in local sandbox, you can also use 'Simulate M-Pesa Payment' below."
        )

    return redirect('booking_checkout', booking_id=booking.id)


@csrf_exempt
def mpesa_callback(request):
    """Safaricom Daraja STK Push Callback Endpoint."""
    if request.method != 'POST':
        return HttpResponse('Method not allowed', status=405)

    try:
        raw_body = request.body.decode('utf-8')
        data = json.loads(raw_body)
        logger.info(f"M-Pesa Callback received: {data}")

        stk_callback = data.get('Body', {}).get('stkCallback', {})
        result_code = stk_callback.get('ResultCode')
        checkout_request_id = stk_callback.get('CheckoutRequestID')

        booking = Booking.objects.filter(checkout_request_id=checkout_request_id).first()
        if booking:
            if result_code == 0:
                callback_meta = stk_callback.get('CallbackMetadata', {}).get('Item', [])
                receipt_number = ''
                for item in callback_meta:
                    if item.get('Name') == 'MpesaReceiptNumber':
                        receipt_number = item.get('Value', '')

                booking.status = 'paid'
                booking.mpesa_receipt = receipt_number or 'MPESA-OK'
                booking.save()
                send_ticket_confirmation_email(booking)
                logger.info(f"Booking {booking.id} marked as PAID via M-Pesa callback. Receipt: {receipt_number}")
            else:
                desc = stk_callback.get('ResultDesc', 'Transaction cancelled')
                logger.warning(f"M-Pesa Payment Failed for booking {booking.id}: {desc}")

        return JsonResponse({"ResultCode": 0, "ResultDesc": "Accepted"})
    except Exception as e:
        logger.error(f"Error handling M-Pesa callback: {e}")
        return JsonResponse({"ResultCode": 1, "ResultDesc": "Internal Error"}, status=500)


@login_required
def check_payment_status(request, booking_id):
    """AJAX polling endpoint for checkout screen."""
    booking = get_object_or_404(Booking, pk=booking_id, user=request.user)
    return JsonResponse({
        'status': booking.status,
        'is_paid': booking.status == 'paid',
        'receipt': booking.mpesa_receipt,
    })


@login_required
def simulate_mpesa_payment(request, booking_id):
    """Simulation helper for development and sandbox environments."""
    booking = get_object_or_404(Booking, pk=booking_id, user=request.user)
    import random
    receipt = f"QGH{random.randint(100000, 999999)}K"
    booking.status = 'paid'
    booking.mpesa_receipt = receipt
    booking.save()
    send_ticket_confirmation_email(booking)
    messages.success(request, f"M-Pesa payment simulated successfully! Receipt: {receipt}. Ticket emailed.")
    return redirect('my_bookings')


@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(user=request.user).select_related('ticket_type__event').order_by('-created_at')
    return render(request, 'bookings/my_bookings.html', {'bookings': bookings})


@login_required
def ticket_qr(request, code):
    booking = get_object_or_404(Booking, code=code)
    if (booking.user != request.user and
            not request.user.is_staff and
            booking.ticket_type.event.organizer != request.user):
        raise Http404("Ticket not found.")

    site_url = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000').rstrip('/')
    checkin_url = f"{site_url}/bookings/tickets/{booking.code}/check-in/"

    qr = qrcode.QRCode(box_size=6, border=2)
    qr.add_data(checkin_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return HttpResponse(buf.getvalue(), content_type='image/png')


@login_required
def mark_as_paid(request, booking_id):
    if not request.user.is_staff:
        messages.error(request, 'Staff permissions required.')
        return redirect('my_bookings')
    booking = get_object_or_404(Booking, pk=booking_id)
    booking.status = 'paid'
    booking.mpesa_receipt = 'STAFF-MANUAL'
    booking.save()
    send_ticket_confirmation_email(booking)
    messages.success(request, f'[TESTING ONLY] Booking {booking.code} marked as PAID. Ticket email dispatched.')
    return redirect('my_bookings')


def check_in_ticket(request, code):
    """
    Gate check-in endpoint: accessed when gate staff or usher scans the QR code.
    Validates payment and marks attendee as checked in, preventing double admissions.
    """
    booking = get_object_or_404(Booking, code=code)

    if booking.status != 'paid':
        status_code = 'unpaid'
    elif booking.checked_in:
        status_code = 'already_used'
    else:
        # First time scan: mark admitted
        booking.checked_in = True
        booking.save()
        status_code = 'admitted'

    return render(request, 'bookings/check_in.html', {
        'booking': booking,
        'status_code': status_code,
    })
