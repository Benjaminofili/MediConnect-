from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    LoginView, PatientRegistrationView, DoctorRegistrationView,
    LogoutView, CurrentUserView, PatientProfileView, DoctorProfileView,
)

app_name = 'accounts'

urlpatterns = [
    path('register/patient/', PatientRegistrationView.as_view(), name='register-patient'),
    path('register/doctor/', DoctorRegistrationView.as_view(), name='register-doctor'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('me/', CurrentUserView.as_view(), name='current-user'),
    path('profile/patient/', PatientProfileView.as_view(), name='patient-profile'),
    path('profile/doctor/', DoctorProfileView.as_view(), name='doctor-profile'),
]