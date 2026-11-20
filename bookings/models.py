import uuid
from django.db import models
from django.conf import settings
from events.models import TicketType

class Booking(models.Model):
    STATUS = [('pending', 'Pending'), ('paid', 'Paid'), ('cancelled', 'Cancelled')]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    ticket_type = models.ForeignKey(TicketType, related_name='bookings', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS, default='pending')
    code = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    checked_in = models.BooleanField(default=False)
    attendee_name = models.CharField(max_length=150, blank=True, default='')
    attendee_email = models.EmailField(blank=True, default='')
    phone_number = models.CharField(max_length=20, blank=True, default='')
    mpesa_receipt = models.CharField(max_length=50, blank=True, default='')
    checkout_request_id = models.CharField(max_length=100, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Booking {self.code} - {self.ticket_type.name} ({self.status})"
