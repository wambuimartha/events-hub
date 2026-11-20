from django.urls import path
from . import views

urlpatterns = [
    path('book/<int:ticket_id>/', views.book_ticket, name='book_ticket'),
    path('checkout/<int:booking_id>/', views.booking_checkout, name='booking_checkout'),
    path('mpesa/pay/<int:booking_id>/', views.mpesa_stk_push, name='mpesa_stk_push'),
    path('mpesa/callback/', views.mpesa_callback, name='mpesa_callback'),
    path('mpesa/status/<int:booking_id>/', views.check_payment_status, name='check_payment_status'),
    path('mpesa/simulate/<int:booking_id>/', views.simulate_mpesa_payment, name='simulate_mpesa_payment'),
    path('my-tickets/', views.my_bookings, name='my_bookings'),
    path('tickets/<uuid:code>/qr/', views.ticket_qr, name='ticket_qr'),
    path('test-mark-paid/<int:booking_id>/', views.mark_as_paid, name='mark_as_paid'),
    path('tickets/<uuid:code>/check-in/', views.check_in_ticket, name='check_in_ticket'),
]
