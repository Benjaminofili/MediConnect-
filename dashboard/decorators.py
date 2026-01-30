# dashboard/decorators.py

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def redirect_authenticated_user(view_func):
    """Redirect authenticated users away from auth pages (login, register, etc.)"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            # User is already logged in, redirect to their dashboard
            if request.user.user_type == 'doctor':
                return redirect('dashboard:doctor_dashboard')
            elif request.user.user_type == 'patient':
                return redirect('dashboard:patient_dashboard')
            else:
                return redirect('admin:index')
        return view_func(request, *args, **kwargs)
    return wrapper


def patient_required(view_func):
    """Ensure user is a patient."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.user_type != 'patient':
            messages.error(request, 'Access denied. Patients only.')
            return redirect('dashboard:login')
        return view_func(request, *args, **kwargs)
    return wrapper


def doctor_required(view_func):
    """Ensure user is a doctor."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.user_type != 'doctor':
            messages.error(request, 'Access denied. Doctors only.')
            return redirect('dashboard:login')
        return view_func(request, *args, **kwargs)
    return wrapper


def email_verified_required(view_func):
    """Ensure user has verified their email."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.email_verified:
            messages.warning(request, 'Please verify your email first.')
            return redirect('dashboard:resend_verification')
        return view_func(request, *args, **kwargs)
    return wrapper