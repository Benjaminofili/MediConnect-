# landing/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json

from landing.models import Service
from .models import Service, Testimonial, FAQ
from accounts.models import DoctorProfile

def home(request):
    """Home/Landing page"""
    # 1. Get Services (Ordered by 'order')
    services = Service.objects.all()[:4] # fetching first 4 services
    
    # 2. Get Verified Doctors (Limit to 8 for the slider) - only show verified doctors
    doctors = DoctorProfile.objects.select_related('user', 'specialization').filter(
        verification_status='verified'
    ).order_by('-average_rating', '-total_reviews')[:8]
    
    # 3. Get Testimonials
    testimonials = Testimonial.objects.all()[:6]  # Limit to 6 for homepage
    
    # 4. Get FAQs
    faqs = FAQ.objects.all()[:6]  # Limit to 6 for homepage
    context = {
        'page_title': 'Mediax - Health & Medical',
        'services': services,
        'doctors': doctors,
        'testimonials': testimonials,
        'faqs': faqs,
    }
    return render(request, 'landing/home.html', context)


def about(request):
    """About Us page"""
    context = {
        'page_title': 'About Us - Mediax',
    }
    return render(request, 'landing/about.html', context)


def contact(request):
    """Contact page"""
    if request.method == 'POST':
        # Handle contact form submission
        name = request.POST.get('name')
        email = request.POST.get('email')
        message_text = request.POST.get('message')
        
        # TODO: Process the contact form (save to DB, send email, etc.)
        
        messages.success(request, 'Your message has been sent successfully!')
        return redirect('landing:contact')
    
    context = {
        'page_title': 'Contact Us - Mediax',
    }
    return render(request, 'landing/contact.html', context)


def services(request):
    """Services listing page"""
    # Get all services ordered by display order
    services = Service.objects.all().order_by('order')
    context = {
        'page_title': 'Our Services - Mediax',
        'services': services,
    }
    return render(request, 'landing/services.html', context)


def service_details(request, service_id=None):
    """Service details page"""
    service = None
    if service_id:
        from django.shortcuts import get_object_or_404
        service = get_object_or_404(Service, id=service_id)
    
    context = {
        'page_title': f'{service.title} - Service Details' if service else 'Service Details - Mediax',
        'service': service,
    }
    return render(request, 'landing/service_details.html', context)



def team(request):
    """Team listing page"""
    # Get all verified doctors
    doctors = DoctorProfile.objects.select_related('user', 'specialization').filter(
        verification_status='verified'
    ).order_by('-average_rating', '-total_reviews')
    context = {
        'page_title': 'Our Team - Mediax',
        'doctors': doctors,
    }
    return render(request, 'landing/team.html', context)


def team_details(request):
    """Team member details page"""
    context = {
        'page_title': 'Doctor Profile - Mediax',
    }
    return render(request, 'landing/team_details.html', context)


def appointment(request):
    """Appointment booking page"""
    # Get verified doctors for the appointment form
    doctors = DoctorProfile.objects.select_related('user', 'specialization').filter(
        verification_status='verified'
    ).order_by('user__first_name')
    
    # Get specializations for the subject dropdown
    from doctors.models import Specialization
    specializations = Specialization.objects.all().order_by('name')
    
    if request.method == 'POST':
        # Handle appointment form submission
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('number')
        department = request.POST.get('subject')
        date = request.POST.get('date')
        time = request.POST.get('time')
        
        # TODO: Process the appointment (save to DB, etc.)
        
        messages.success(request, 'Your appointment has been booked successfully!')
        return redirect('landing:appointment')
    
    context = {
        'page_title': 'Book Appointment - Mediax',
        'doctors': doctors,
        'specializations': specializations,
    }
    return render(request, 'landing/appointment.html', context)


def faq(request):
    """FAQ page"""
    # Get all FAQs ordered by display order
    faqs = FAQ.objects.all().order_by('order')
    context = {
        'page_title': 'FAQ - Mediax',
        'faqs': faqs,
    }
    return render(request, 'landing/faq.html', context)


# Form submission handlers
@require_POST
def newsletter_subscribe(request):
    """Handle newsletter subscription"""
    email = request.POST.get('email')
    # TODO: Save to newsletter list
    messages.success(request, 'Successfully subscribed to newsletter!')
    return redirect(request.META.get('HTTP_REFERER', 'landing:home'))


@require_POST  
def appointment_submit(request):
    """Handle appointment form submission via AJAX"""
    try:
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('number')
        department = request.POST.get('subject')
        date = request.POST.get('date')
        time = request.POST.get('time')
        
        # TODO: Save appointment to database
        
        return JsonResponse({
            'success': True,
            'message': 'Appointment booked successfully!'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)