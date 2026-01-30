# accounts/views.py
from django.contrib.auth import get_user_model, login as auth_login, logout as auth_logout
from django.http import Http404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from notifications.services import EmailService
from .models import PatientProfile, DoctorProfile
from .serializers import (
    CustomTokenObtainPairSerializer, UserSerializer,
    PatientRegistrationSerializer, DoctorRegistrationSerializer,
    PatientProfileSerializer, DoctorProfileSerializer,
)

User = get_user_model()


class LoginView(TokenObtainPairView):
    """
    Login view that returns JWT tokens AND creates a Django session.
    This allows both API authentication (JWT) and page access (@login_required).
    """
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            # Get the user and create Django session
            email = request.data.get('email')
            try:
                user = User.objects.get(email=email)
                auth_login(request, user)
            except User.DoesNotExist:
                pass
        
        return response


class PatientRegistrationView(generics.CreateAPIView):
    """Register a new patient account."""
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = PatientRegistrationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        # Create Django session (so @login_required works)
        auth_login(request, user)
        
        # Send welcome email
        try:
            EmailService.send_welcome_email(user)
        except Exception as e:
            print(f"Failed to send welcome email: {e}")
        
        return Response({
            'message': 'Registration successful',
            'user': {
                'id': user.id,
                'email': user.email,
                'full_name': user.full_name,
                'user_type': user.user_type
            },
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token)
            }
        }, status=status.HTTP_201_CREATED)


class DoctorRegistrationView(generics.CreateAPIView):
    """Register a new doctor account."""
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = DoctorRegistrationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        # Create Django session
        auth_login(request, user)
        
        # Send welcome email
        try:
            EmailService.send_welcome_email(user)
        except Exception as e:
            print(f"Failed to send welcome email: {e}")
        
        return Response({
            'message': 'Registration successful. Pending verification.',
            'user': {
                'id': user.id,
                'email': user.email,
                'full_name': user.full_name,
                'user_type': user.user_type
            },
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token)
            }
        }, status=status.HTTP_201_CREATED)


class LogoutView(APIView):
    """Logout - blacklist JWT token and clear Django session."""
    permission_classes = [permissions.AllowAny]  # Allow logout even if token expired

    def post(self, request):
        # Try to blacklist JWT token
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
        except Exception as e:
            print(f"Token blacklist error: {e}")
        
        # Always clear Django session
        auth_logout(request)
        
        return Response({'message': 'Logged out successfully'})


class CurrentUserView(generics.RetrieveUpdateAPIView):
    """Get or update current user information."""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class PatientProfileView(generics.RetrieveUpdateAPIView):
    """Get or update patient profile."""
    serializer_class = PatientProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        profile, _ = PatientProfile.objects.get_or_create(user=self.request.user)
        return profile


class DoctorProfileView(generics.RetrieveUpdateAPIView):
    """Get or update doctor profile."""
    serializer_class = DoctorProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        try:
            return self.request.user.doctor_profile
        except DoctorProfile.DoesNotExist:
            raise Http404("Doctor profile not found. Only doctors can access this endpoint.")