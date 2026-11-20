from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Booking
from .email import send_ticket_confirmation_email


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'ticket_code',
        'event_name',
        'attendee_display',
        'attendee_email',
        'phone_number',
        'ticket_type_name',
        'quantity',
        'formatted_total',
        'status_badge',
        'check_in_badge',
        'created_at',
    )
    list_filter = ('status', 'checked_in', 'ticket_type__event', 'created_at')
    search_fields = (
        'code',
        'attendee_name',
        'attendee_email',
        'phone_number',
        'user__username',
        'user__email',
        'mpesa_receipt',
        'ticket_type__event__title',
    )
    readonly_fields = ('code', 'created_at')
    ordering = ('-created_at',)
    actions = ['mark_as_paid', 'mark_as_checked_in', 'resend_email']

    @admin.display(description='Ticket Code')
    def ticket_code(self, obj):
        return format_html(
            '<span style="font-family: monospace; font-weight: bold; background: #F1F5F9; padding: 2px 6px; border-radius: 4px;">#{}</span>',
            str(obj.code)[:8]
        )

    @admin.display(description='Event')
    def event_name(self, obj):
        event = obj.ticket_type.event
        url = reverse('admin:events_event_change', args=[event.id])
        return format_html('<a href="{}" style="font-weight: 600; color: #2563EB;">{}</a>', url, event.title[:30])

    @admin.display(description='Attendee')
    def attendee_display(self, obj):
        return obj.attendee_name or obj.user.get_full_name() or obj.user.username

    @admin.display(description='Pass Tier')
    def ticket_type_name(self, obj):
        return obj.ticket_type.name

    @admin.display(description='Total')
    def formatted_total(self, obj):
        if obj.total == 0:
            return format_html('<span style="color: #059669; font-weight: bold;">FREE</span>')
        return format_html('KSh {}', f"{obj.total:,.0f}")

    @admin.display(description='Status')
    def status_badge(self, obj):
        if obj.status == 'paid':
            return format_html('<span style="background: #ECFDF5; color: #059669; font-weight: bold; padding: 3px 8px; border-radius: 9999px; font-size: 11px;">PAID ({})</span>', obj.mpesa_receipt or 'OK')
        elif obj.status == 'pending':
            return format_html('<span style="background: #FEF3C7; color: #B45309; font-weight: bold; padding: 3px 8px; border-radius: 9999px; font-size: 11px;">PENDING</span>')
        return format_html('<span style="background: #FEE2E2; color: #B91C1C; font-weight: bold; padding: 3px 8px; border-radius: 9999px; font-size: 11px;">{}</span>', obj.status.upper())

    @admin.display(description='Gate Check-in')
    def check_in_badge(self, obj):
        if obj.checked_in:
            return format_html('<span style="color: #10B981; font-weight: bold;">&#10003; Checked In</span>')
        return format_html('<span style="color: #94A3B8;">&mdash; Not yet</span>')

    @admin.action(description='Mark selected bookings as PAID & dispatch ticket email')
    def mark_as_paid(self, request, queryset):
        count = 0
        for booking in queryset:
            if booking.status != 'paid':
                booking.status = 'paid'
                if not booking.mpesa_receipt:
                    booking.mpesa_receipt = 'ADMIN-CONFIRMED'
                booking.save()
                send_ticket_confirmation_email(booking)
                count += 1
        self.message_user(request, f"Successfully marked {count} booking(s) as PAID and dispatched confirmation emails.")

    @admin.action(description='Mark selected bookings as CHECKED IN at gate')
    def mark_as_checked_in(self, request, queryset):
        updated = queryset.update(checked_in=True)
        self.message_user(request, f"Successfully marked {updated} attendee(s) as CHECKED IN.")

    @admin.action(description='Resend ticket confirmation email to attendees')
    def resend_email(self, request, queryset):
        sent = 0
        for booking in queryset:
            send_ticket_confirmation_email(booking)
            sent += 1
        self.message_user(request, f"Dispatched confirmation emails to {sent} attendee(s).")
