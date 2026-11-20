from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import Event


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
