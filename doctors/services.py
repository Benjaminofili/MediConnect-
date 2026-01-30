from datetime import datetime, timedelta
from django.utils import timezone
from .models import Availability, TimeSlot


def generate_time_slots(doctor_profile, days_ahead=30):
    """
    Generate time slots for a doctor based on their availability template.
    Uses bulk_create for better performance.
    """
    
    # Get doctor's active availability
    availabilities = Availability.objects.filter(
        doctor=doctor_profile,
        is_active=True
    )
    
    if not availabilities.exists():
        return 0
    
    today = timezone.now().date()
    slot_duration = timedelta(minutes=30)
    
    # Get existing slots to avoid duplicates
    existing_slots = set(
        TimeSlot.objects.filter(
            doctor=doctor_profile,
            date__gte=today,
            date__lte=today + timedelta(days=days_ahead)
        ).values_list('date', 'start_time')
    )
    
    # Collect all new slots
    new_slots = []
    
    # Generate for each day
    for day_offset in range(days_ahead):
        current_date = today + timedelta(days=day_offset)
        day_of_week = current_date.weekday()
        
        # Get availability for this day of week
        day_availability = availabilities.filter(day_of_week=day_of_week)
        
        for availability in day_availability:
            # Create datetime objects for the time window
            start_datetime = datetime.combine(current_date, availability.start_time)
            end_datetime = datetime.combine(current_date, availability.end_time)
            current_slot_time = start_datetime
            
            # Generate 30-minute slots
            while current_slot_time + slot_duration <= end_datetime:
                slot_start = current_slot_time.time()
                slot_end = (current_slot_time + slot_duration).time()
                
                # Check if slot already exists
                if (current_date, slot_start) not in existing_slots:
                    new_slots.append(
                        TimeSlot(
                            doctor=doctor_profile,
                            date=current_date,
                            start_time=slot_start,
                            end_time=slot_end,
                            status='available'
                        )
                    )
                
                current_slot_time += slot_duration
    
    # Bulk create all slots at once
    if new_slots:
        TimeSlot.objects.bulk_create(new_slots, ignore_conflicts=True)
    
    return len(new_slots)


def generate_all_doctor_slots(days_ahead=30):
    """Generate slots for all verified doctors"""
    
    from accounts.models import DoctorProfile
    
    doctors = DoctorProfile.objects.filter(verification_status='verified')
    total_slots = 0
    
    for doctor in doctors:
        slots = generate_time_slots(doctor, days_ahead)
        total_slots += slots
    
    return total_slots