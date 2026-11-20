from django.db import models
from django.conf import settings

class Event(models.Model):
    organizer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    venue = models.CharField(max_length=200)
    start_time = models.DateTimeField()
    banner = models.ImageField(upload_to='banners/', blank=True)
    is_published = models.BooleanField(default=True)

    def __str__(self):
        return self.title

    @property
    def banner_url(self):
        if not self.banner:
            return ''
        name = str(self.banner)
        file_path = settings.MEDIA_ROOT / name
        if not file_path.exists():
            base = file_path.with_suffix('')
            for ext in ['.png', '.jpg', '.jpeg', '.webp']:
                candidate = base.with_suffix(ext)
                if candidate.exists():
                    rel = candidate.relative_to(settings.MEDIA_ROOT).as_posix()
                    return f"{settings.MEDIA_URL}{rel}"
        return self.banner.url

class TicketType(models.Model):
    event = models.ForeignKey(Event, related_name='ticket_types', on_delete=models.CASCADE)
    name = models.CharField(max_length=50)        # Regular, VIP, Early Bird
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.event.title} - {self.name}"

    @property
    def remaining(self):
        sold = sum(b.quantity for b in self.bookings.filter(status='paid'))
        return self.quantity - sold
