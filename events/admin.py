from django.contrib import admin
from .models import Event, TicketType

class TicketTypeInline(admin.TabularInline):
    model = TicketType
    extra = 1

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'organizer', 'venue', 'start_time', 'is_published')
    list_filter = ('is_published', 'start_time')
    search_fields = ('title', 'venue', 'description')
    inlines = [TicketTypeInline]

@admin.register(TicketType)
class TicketTypeAdmin(admin.ModelAdmin):
    list_display = ('event', 'name', 'price', 'quantity', 'remaining')
    list_filter = ('event',)
    search_fields = ('name', 'event__title')
