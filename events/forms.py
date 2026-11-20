from django import forms
from .models import Event, TicketType


class EventCreateForm(forms.ModelForm):
    start_time = forms.DateTimeField(
        label="Event Date & Time (EAT)",
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'clean-input',
        })
    )

    # Primary Ticket Tier
    ticket_name = forms.CharField(
        max_length=50,
        initial="Regular Pass",
        label="Primary Pass Tier Name",
        widget=forms.TextInput(attrs={'class': 'clean-input', 'placeholder': 'e.g. Regular Pass / Free Student Entry'})
    )
    ticket_price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        initial=0.00,
        label="Ticket Price (KSh, 0 for Free)",
        widget=forms.NumberInput(attrs={'class': 'clean-input', 'placeholder': '0.00'})
    )
    ticket_quantity = forms.IntegerField(
        initial=100,
        min_value=1,
        label="Total Available Passes",
        widget=forms.NumberInput(attrs={'class': 'clean-input', 'placeholder': '100'})
    )

    # Optional Second Tier (e.g. VIP)
    vip_ticket_name = forms.CharField(
        max_length=50,
        required=False,
        label="Optional 2nd Tier Name (e.g. VIP / Front Row)",
        widget=forms.TextInput(attrs={'class': 'clean-input', 'placeholder': 'Leave empty if single tier'})
    )
    vip_ticket_price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        label="VIP Ticket Price (KSh)",
        widget=forms.NumberInput(attrs={'class': 'clean-input', 'placeholder': '500.00'})
    )
    vip_ticket_quantity = forms.IntegerField(
        required=False,
        min_value=1,
        label="VIP Quantity",
        widget=forms.NumberInput(attrs={'class': 'clean-input', 'placeholder': '50'})
    )

    class Meta:
        model = Event
        fields = ['title', 'venue', 'start_time', 'banner', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'clean-input', 'placeholder': 'e.g. Nairobi Campus AI Hackathon 2026'}),
            'venue': forms.TextInput(attrs={'class': 'clean-input', 'placeholder': 'e.g. University of Nairobi - Taifa Hall'}),
            'description': forms.Textarea(attrs={'class': 'clean-input', 'rows': 4, 'placeholder': 'Describe what attendees can expect...'}),
        }
