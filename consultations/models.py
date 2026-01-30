from django.db import models
from django.utils import timezone
import random
import string
from records.models import PrivateMediaStorage


class Consultation(models.Model):
    """Consultation record for a completed appointment."""
    
    appointment = models.OneToOneField(
        'appointments.Appointment',
        on_delete=models.CASCADE,
        related_name='consultation'
    )
    
    # Consultation details
    chief_complaint = models.TextField(blank=True, help_text="Main reason for visit")
    symptoms = models.TextField(blank=True, help_text="Symptoms described by patient")
    examination_notes = models.TextField(blank=True, help_text="Physical examination findings")
    diagnosis = models.TextField(blank=True, help_text="Doctor's diagnosis")
    treatment_plan = models.TextField(blank=True, help_text="Recommended treatment")
    
    # Doctor's notes
    notes = models.TextField(blank=True, help_text="Additional notes")
    private_notes = models.TextField(blank=True, help_text="Private notes (only visible to doctor)")
    
    # Follow-up
    followup_needed = models.BooleanField(default=False)
    followup_date = models.DateField(null=True, blank=True)
    followup_notes = models.TextField(blank=True)
    
    # Timing
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Consultation: {self.appointment.appointment_number}"
    
    @property
    def duration_minutes(self):
        """Calculate consultation duration in minutes."""
        if self.started_at and self.ended_at:
            delta = self.ended_at - self.started_at
            return int(delta.total_seconds() / 60)
        return None


class Prescription(models.Model):
    """Prescription issued during consultation."""
    
    consultation = models.ForeignKey(
        Consultation,
        on_delete=models.CASCADE,
        related_name='prescriptions'
    )
    
    prescription_number = models.CharField(max_length=20, unique=True, blank=True)
    diagnosis = models.TextField(blank=True)
    notes = models.TextField(blank=True, help_text="Additional instructions")
    pdf_file = models.FileField(upload_to='prescriptions/%Y/%m/', storage=PrivateMediaStorage(), blank=True, null=True, help_text="Uploaded PDF of the prescription")
    
    # Validity
    issued_date = models.DateField(auto_now_add=True)
    valid_until = models.DateField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Prescription: {self.prescription_number}"
    
    def save(self, *args, **kwargs):
        if not self.prescription_number:
            self.prescription_number = self.generate_prescription_number()
        super().save(*args, **kwargs)
    
    def generate_prescription_number(self):
        """Generate unique prescription number: RX-YYYYMMDD-XXXX"""
        date_str = timezone.now().strftime('%Y%m%d')
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        return f"RX-{date_str}-{random_str}"


class PrescriptionItem(models.Model):
    """Individual medicine in a prescription."""
    
    FREQUENCY_CHOICES = [
        ('once_daily', 'Once Daily'),
        ('twice_daily', 'Twice Daily'),
        ('three_times_daily', 'Three Times Daily'),
        ('four_times_daily', 'Four Times Daily'),
        ('every_4_hours', 'Every 4 Hours'),
        ('every_6_hours', 'Every 6 Hours'),
        ('every_8_hours', 'Every 8 Hours'),
        ('every_12_hours', 'Every 12 Hours'),
        ('as_needed', 'As Needed'),
        ('before_meals', 'Before Meals'),
        ('after_meals', 'After Meals'),
        ('at_bedtime', 'At Bedtime'),
        ('other', 'Other (See Instructions)'),
    ]
    
    DURATION_CHOICES = [
        ('3_days', '3 Days'),
        ('5_days', '5 Days'),
        ('7_days', '7 Days'),
        ('10_days', '10 Days'),
        ('14_days', '14 Days'),
        ('21_days', '21 Days'),
        ('30_days', '30 Days'),
        ('60_days', '60 Days'),
        ('90_days', '90 Days'),
        ('ongoing', 'Ongoing'),
        ('other', 'Other (See Instructions)'),
    ]
    
    prescription = models.ForeignKey(
        Prescription,
        on_delete=models.CASCADE,
        related_name='items'
    )
    
    medicine_name = models.CharField(max_length=200)
    dosage = models.CharField(max_length=100, help_text="e.g., 500mg, 10ml")
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    duration = models.CharField(max_length=20, choices=DURATION_CHOICES)
    quantity = models.CharField(max_length=50, blank=True, help_text="e.g., 30 tablets")
    instructions = models.TextField(blank=True, help_text="Special instructions")
    
    class Meta:
        ordering = ['id']
    
    def __str__(self):
        return f"{self.medicine_name} - {self.dosage}"