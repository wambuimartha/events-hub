import shutil
from pathlib import Path
from django.apps import AppConfig
from django.conf import settings


class EventsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'events'

    def ready(self):
        try:
            src = settings.MEDIA_ROOT / 'logo' / 'EventHub Campus Edition Logo.png'
            if src.exists():
                dst = settings.MEDIA_ROOT / 'logo' / 'logo.png'
                if not dst.exists() or dst.stat().st_size != src.stat().st_size:
                    shutil.copy2(src, dst)
                static_dst = settings.BASE_DIR / 'static' / 'images' / 'logo.png'
                static_dst.parent.mkdir(parents=True, exist_ok=True)
                if not static_dst.exists() or static_dst.stat().st_size != src.stat().st_size:
                    shutil.copy2(src, static_dst)
        except Exception:
            pass
