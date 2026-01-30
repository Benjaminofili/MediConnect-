from django.urls import path
from .views import (
    BookAppointmentView,
    MyAppointmentsView,
    UpcomingAppointmentsView,
    AppointmentDetailView,
    CancelAppointmentView,
    RescheduleAppointmentView,
    JoinConsultationView,
    CompleteAppointmentView,
    DoctorTodayAppointmentsView,
)

urlpatterns = [
    # Booking
    path('book/', BookAppointmentView.as_view(), name='book-appointment'),
    
    # List appointments
    path('', MyAppointmentsView.as_view(), name='my-appointments'),
    path('upcoming/', UpcomingAppointmentsView.as_view(), name='upcoming-appointments'),
    path('today/', DoctorTodayAppointmentsView.as_view(), name='today-appointments'),
    
    # Single appointment
    path('<int:pk>/', AppointmentDetailView.as_view(), name='appointment-detail'),
    
    # Actions
    path('<int:pk>/cancel/', CancelAppointmentView.as_view(), name='cancel-appointment'),
    path('<int:pk>/reschedule/', RescheduleAppointmentView.as_view(), name='reschedule-appointment'),
    path('<int:pk>/join/', JoinConsultationView.as_view(), name='join-consultation'),
    path('<int:pk>/complete/', CompleteAppointmentView.as_view(), name='complete-appointment'),
]