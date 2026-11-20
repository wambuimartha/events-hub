from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Sum
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Event, TicketType
from .forms import EventCreateForm
from bookings.models import Booking


def event_list(request):
    query = request.GET.get('q', '').strip()
    category = request.GET.get('category', '').strip()
    events = Event.objects.filter(is_published=True).prefetch_related('ticket_types')

    if query:
        events = events.filter(
            Q(title__icontains=query) |
            Q(venue__icontains=query) |
            Q(description__icontains=query)
        )
    
    if category and category.lower() != 'all':
        cat_lower = category.lower()
        if cat_lower == 'free':
            events = events.filter(ticket_types__price=0)
        elif cat_lower in ['tech', 'hackathon']:
            events = events.filter(Q(title__icontains='tech') | Q(title__icontains='hack') | Q(description__icontains='tech'))
        elif cat_lower in ['parties', 'party', 'bash']:
            events = events.filter(Q(title__icontains='bash') | Q(title__icontains='neon') | Q(title__icontains='disco') | Q(description__icontains='dj'))
        elif cat_lower in ['sports', 'rugby']:
            events = events.filter(Q(title__icontains='sport') | Q(title__icontains='rugby') | Q(description__icontains='varsity'))
        elif cat_lower in ['career', 'talks']:
            events = events.filter(Q(title__icontains='career') | Q(title__icontains='internship') | Q(description__icontains='career'))
        elif cat_lower in ['arts', 'culture', 'gala']:
            events = events.filter(Q(title__icontains='gala') | Q(title__icontains='culture') | Q(title__icontains='fashion'))
        else:
            events = events.filter(Q(title__icontains=category) | Q(description__icontains=category))

    events = events.distinct().order_by('start_time')
    return render(request, 'events/event_list.html', {
        'events': events,
        'query': query,
        'selected_category': category
    })


def event_detail(request, pk):
    event = get_object_or_404(Event, pk=pk, is_published=True)
    return render(request, 'events/event_detail.html', {'event': event})


@login_required
def create_event(request):
    """
    Organizer / Admin portal view to upload new campus events and ticket tiers.
    """
    if not request.user.is_staff:
        messages.error(request, "Staff / Organizer permissions are required to upload events.")
        return redirect('event_list')

    if request.method == 'POST':
        form = EventCreateForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.organizer = request.user
            event.save()

            # Create primary ticket tier
            TicketType.objects.create(
                event=event,
                name=form.cleaned_data['ticket_name'],
                price=form.cleaned_data['ticket_price'],
                quantity=form.cleaned_data['ticket_quantity']
            )

            # Create optional VIP ticket tier
            vip_name = form.cleaned_data.get('vip_ticket_name', '').strip()
            if vip_name and form.cleaned_data.get('vip_ticket_price') is not None and form.cleaned_data.get('vip_ticket_quantity'):
                TicketType.objects.create(
                    event=event,
                    name=vip_name,
                    price=form.cleaned_data['vip_ticket_price'],
                    quantity=form.cleaned_data['vip_ticket_quantity']
                )

            messages.success(request, f"Event '{event.title}' was successfully published!")
            return redirect('event_detail', pk=event.pk)
    else:
        form = EventCreateForm()

    return render(request, 'events/event_create.html', {'form': form})


@login_required
def organizer_portal(request):
    """
    Campus Organizer & Staff Admin Portal.
    Displays live KPI metrics, attendee registration roster,
    ticket revenue, and event management controls.
    """
    if not request.user.is_staff:
        messages.error(request, "Staff / Organizer permissions are required to access the Admin Portal.")
        return redirect('event_list')

    events = Event.objects.all().order_by('-start_time')

    event_id = request.GET.get('event_id', '').strip()
    status_filter = request.GET.get('status', '').strip()
    search_query = request.GET.get('q', '').strip()

    bookings = Booking.objects.select_related('ticket_type__event', 'user').order_by('-created_at')

    if event_id:
        bookings = bookings.filter(ticket_type__event_id=event_id)
    if status_filter:
        bookings = bookings.filter(status=status_filter)
    if search_query:
        bookings = bookings.filter(
            Q(attendee_name__icontains=search_query) |
            Q(attendee_email__icontains=search_query) |
            Q(phone_number__icontains=search_query) |
            Q(code__icontains=search_query) |
            Q(mpesa_receipt__icontains=search_query) |
            Q(user__username__icontains=search_query)
        )

    # Metrics
    total_bookings = Booking.objects.count()
    paid_bookings = Booking.objects.filter(status='paid')
    total_paid_count = paid_bookings.count()
    total_revenue = paid_bookings.aggregate(total=Sum('total'))['total'] or 0
    total_checked_in = Booking.objects.filter(checked_in=True).count()
    total_events = Event.objects.count()

    return render(request, 'events/portal.html', {
        'events': events,
        'bookings': bookings[:100],
        'total_bookings': total_bookings,
        'total_paid_count': total_paid_count,
        'total_revenue': total_revenue,
        'total_checked_in': total_checked_in,
        'total_events': total_events,
        'selected_event_id': event_id,
        'selected_status': status_filter,
        'search_query': search_query,
    })
