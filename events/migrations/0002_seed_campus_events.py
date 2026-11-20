from datetime import timedelta
from decimal import Decimal
from django.db import migrations
from django.utils import timezone


def seed_campus_events(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    Event = apps.get_model('events', 'Event')
    TicketType = apps.get_model('events', 'TicketType')

    # Get or create default organizer
    organizer = User.objects.filter(is_superuser=True).first()
    if not organizer:
        organizer = User.objects.filter(username='martha').first()
    if not organizer:
        organizer = User.objects.create(username='campus_admin', email='admin@campus.eventhub.co.ke')

    # Remove previous initial seed to cleanly transition to Campus Edition
    Event.objects.all().delete()

    now = timezone.now()

    campus_events = [
        {
            'title': 'Campus HackFest & AI Buildathon 2026',
            'description': 'Join 500+ student developers, designers, and innovators from UoN, JKUAT, Strathmore, and across Kenya for a 48-hour buildathon! Build cutting-edge solutions, win KSh 250,000 in bounties, and connect with tech recruiters. Free meals, swag, and cloud credits included.',
            'venue': 'University of Nairobi (UoN) - Chiromo Science Complex',
            'start_time': now + timedelta(days=5, hours=9),
            'banner': 'banners/tech_summit.jpg',
            'tickets': [
                {'name': 'Student Hacker Pass', 'price': Decimal('0.00'), 'quantity': 350},
                {'name': 'Mentor & Judge Pass', 'price': Decimal('0.00'), 'quantity': 50},
            ]
        },
        {
            'title': "Freshers' Neon Bash & DJ Concert",
            'description': "The biggest semester opening party in Nairobi! Featuring Kenya's top campus DJs, neon paint stations, hype hosts, and live guest artist performances. Dress code: Neon glow or all-white. Strictly 18+ student ID required at the gate.",
            'venue': 'Kenyatta University (KU) - Amphitheatre Grounds, Thika Rd',
            'start_time': now + timedelta(days=9, hours=19),
            'banner': 'banners/afrobeats.jpg',
            'tickets': [
                {'name': 'Early Bird Pass', 'price': Decimal('300.00'), 'quantity': 200},
                {'name': 'Regular Ticket', 'price': Decimal('500.00'), 'quantity': 600},
                {'name': 'Squad VIP Pass (4 Guests)', 'price': Decimal('1500.00'), 'quantity': 30},
            ]
        },
        {
            'title': 'Inter-Varsity Rugby Derby & Street Food Fest',
            'description': 'Witness intense varsity rugby rivalries as Mean Machine takes on Blak Blad, Strathmore Leos, and Daystar Falcons! Surrounding the pitch will be a massive street food carnival with 20+ campus foodie stalls, mocktails, and live acoustic music.',
            'venue': 'Strathmore University Sports Complex - Madaraka',
            'start_time': now + timedelta(days=12, hours=11),
            'banner': 'banners/culinary.jpg',
            'tickets': [
                {'name': 'General Fan Admission', 'price': Decimal('0.00'), 'quantity': 500},
                {'name': 'Pitchside Bleachers + Food Voucher', 'price': Decimal('350.00'), 'quantity': 150},
            ]
        },
        {
            'title': 'Campus Career & Tech Internship Expo',
            'description': 'Connect face-to-face with top employers, fintech leaders, and startups hiring interns and graduate trainees across East Africa. Includes free CV clinics, mock technical interviews, and LinkedIn headshot booths.',
            'venue': 'JKUAT Main Campus - Juja Assembly Hall',
            'start_time': now + timedelta(days=16, hours=8, minutes=30),
            'banner': 'banners/cybersecurity.jpg',
            'tickets': [
                {'name': 'Student All-Access Pass', 'price': Decimal('0.00'), 'quantity': 800},
            ]
        },
        {
            'title': 'Mr & Miss Campus Gala & Cultural Runway',
            'description': 'An evening of haute couture, campus talent, live orchestra, and cultural celebration. Cheer on your university representatives as they compete for the 2026 Campus Crown and ambassador awards. Red carpet cocktails start at 6:00 PM.',
            'venue': 'USIU-Africa - Main Auditorium, Roysambu',
            'start_time': now + timedelta(days=20, hours=18),
            'banner': 'banners/gala.jpg',
            'tickets': [
                {'name': 'Standard Entry', 'price': Decimal('400.00'), 'quantity': 300},
                {'name': 'VIP Front Row + Cocktail', 'price': Decimal('1000.00'), 'quantity': 50},
            ]
        },
        {
            'title': 'End of Semester Silent Disco & Outdoor Cinema',
            'description': 'Wind down after final exams! 3 DJ channels (Afrobeats, Amapiano, EDM & Hip Hop) with wireless glowing headphones, picnic blankets under the stars, followed by a midnight outdoor cinema screening.',
            'venue': 'The Hub Grounds & Gardens - Karen (Near CUEA & Co-operative Univ)',
            'start_time': now + timedelta(days=27, hours=19, minutes=30),
            'banner': 'banners/midnight_glow.jpg',
            'tickets': [
                {'name': 'Early Bird Headphone Pass', 'price': Decimal('600.00'), 'quantity': 150},
                {'name': 'Gate Admission', 'price': Decimal('900.00'), 'quantity': 250},
            ]
        },
    ]

    for item in campus_events:
        tickets_data = item.pop('tickets')
        event = Event.objects.create(organizer=organizer, is_published=True, **item)
        for t in tickets_data:
            TicketType.objects.create(event=event, **t)


def unseed_campus_events(apps, schema_editor):
    Event = apps.get_model('events', 'Event')
    Event.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_campus_events, unseed_campus_events),
    ]
