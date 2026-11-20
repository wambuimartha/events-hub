from django.urls import path
from . import views

urlpatterns = [
    path('', views.event_list, name='event_list'),
    path('portal/', views.organizer_portal, name='organizer_portal'),
    path('portal/bookings/<int:booking_id>/resend/', views.resend_portal_email, name='resend_portal_email'),
    path('events/create/', views.create_event, name='create_event'),
    path('events/<int:pk>/', views.event_detail, name='event_detail'),
]
