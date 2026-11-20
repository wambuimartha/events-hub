from django.contrib import admin
from .models import Booking

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'code', 'user', 'ticket_type', 'quantity', 'total', 
        'status', 'mpesa_receipt', 'phone_number', 'checked_in', 'created_at'
    )
    list_filter = ('status', 'checked_in', 'created_at')
    search_fields = ('code', 'user__username', 'mpesa_receipt', 'phone_number', 'ticket_type__event__title')
    readonly_fields = ('code', 'created_at')
