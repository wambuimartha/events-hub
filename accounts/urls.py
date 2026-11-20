from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup, name='signup'),
    # Google OAuth2 (commented out for now)
    # path('google/', views.google_login, name='google_login'),
    # path('google/callback/', views.google_callback, name='google_callback'),
]
