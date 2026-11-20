from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Sum, Count, Q
from .models import Event, TicketType


class TicketTypeInline(admin.TabularInline):
    model = TicketType
    extra = 1
    fields = ('name', 'price', 'quantity')


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        'title', 
        'organizer', 
        'venue', 
        'start_time', 
        'total_bookings_count',
        'revenue_generated',
        'is_published'
    )
    list_filter = ('is_published', 'start_time')
    search_fields = ('title', 'venue', 'description', 'organizer__username')
    inlines = [TicketTypeInline]

    @admin.display(description='Attendees Booked')
    def total_bookings_count(self, obj):
        count = obj.ticket_types.aggregate(
            booked=Count('bookings', filter=Q(bookings__status='paid'))
        )['booked'] or 0
        return format_html('<strong>{}</strong> paid attendee(s)', count)

    @admin.display(description='Total Revenue')
    def revenue_generated(self, obj):
        total = obj.ticket_types.aggregate(
            revenue=Sum('bookings__total', filter=Q(bookings__status='paid'))
        )['revenue'] or 0
        return format_html('<span style="color: #059669; font-weight: bold;">KSh {}</span>', f"{total:,.0f}")


@admin.register(TicketType)
class TicketTypeAdmin(admin.ModelAdmin):
    list_display = ('event', 'name', 'price', 'quantity', 'remaining')
    list_filter = ('event',)
    search_fields = ('name', 'event__title')
