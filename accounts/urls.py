from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('home/', views.home, name='home'),
    path('booking/', views.booking_dashboard, name='booking_dashboard'),
    path('book-session/', views.book_session, name='book_session'),
    path('start-experiment/<int:booking_id>/', views.start_experiment, name='start_experiment'),
    path('cancel-booking/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
    path('api/available-slots/', views.get_available_slots, name='available_slots'),
    path('trigger-service/', views.trigger_service, name='trigger_service'),
    path('profile/', views.profile_view, name='profile'),
    path('add-experiment/', views.add_experiment, name='add_experiment'),
]


