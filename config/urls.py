# config/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    return Response({
        'status': 'healthy',
        'message': 'MediConnect API is running'
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request):
    return Response({
        'message': 'Welcome to MediConnect API',
        'version': '1.0.0',
        'endpoints': {
            'auth': '/api/auth/',
            'doctors': '/api/doctors/',
            'appointments': '/api/appointments/',
            'records': '/api/records/',
            'consultations': '/api/consultations/',
        }
    })

def redirect_verify_email(request, uidb64, token):
    return redirect('dashboard:verify_email', uidb64=uidb64, token=token)

def redirect_reset_password(request, uidb64, token):
    return redirect('dashboard:reset_password', uidb64=uidb64, token=token)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
     # Dashboard (protected area)
    path('', include('dashboard.urls')),
    path('verify-email/<uidb64>/<token>/', redirect_verify_email),
    path('reset-password/<uidb64>/<token>/', redirect_reset_password),
    path('accounts/', include('django.contrib.auth.urls')),
    
    # API Routes
    path('api/', api_root, name='api-root'),
    path('api/auth/', include('accounts.urls')),
    path('api/doctors/', include('doctors.urls')),
    path('api/appointments/', include('appointments.urls')),
    path('api/records/', include('records.urls')),
    path('api/consultations/', include('consultations.urls')),
    
    # Health check
    path('health/', health_check, name='health-check'),
    
    # Frontend (catch-all should be last)
    # path('', include('frontend.urls')),

     # Landing pages (frontend) - This should be last as catch-all
    path('', include('landing.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)