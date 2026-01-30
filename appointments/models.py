from django.conf import settings
from django.db import models
from django.utils import timezone
import random
import string


class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]

    # Appointment identifier
    appointment_number = models.CharField(max_length=20, unique=True, blank=True)
    
    # Relationships
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='patient_appointments'
    )
    doctor = models.ForeignKey(
        'accounts.DoctorProfile',
        on_delete=models.CASCADE,
        related_name='doctor_appointments'
    )
    time_slot = models.OneToOneField(
        'doctors.TimeSlot',
        on_delete=models.SET_NULL,  # ← Changed from CASCADE
        related_name='appointment',
        null=True,                   # ← Added
        blank=True                   # ← Added
    )
    
    # Appointment details
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='confirmed')
    reason = models.TextField(blank=True, help_text="Reason for visit")
    symptoms = models.TextField(blank=True, help_text="Describe your symptoms")
    
    # Video consultation
    video_room_url = models.CharField(max_length=500, blank=True)
    video_room_id = models.CharField(max_length=50, blank=True)
    video_host_url = models.CharField(max_length=500, blank=True)

    # Cancellation
    cancellation_reason = models.TextField(blank=True)
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cancelled_appointments'
    )
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    # Reschedule tracking
    rescheduled_from = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rescheduled_to'
    )
    reschedule_count = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-start_time']

    def __str__(self):
        return f"{self.appointment_number} - {self.patient.email} with Dr. {self.doctor.user.last_name}"

    def save(self, *args, **kwargs):
        # Generate appointment number if not exists
        if not self.appointment_number:
            self.appointment_number = self.generate_appointment_number()
        
        # Generate video room if confirmed and no room exists
        # if self.status == 'confirmed' and not self.video_room_id:
        #     self.generate_video_room()
        
        super().save(*args, **kwargs)

    def generate_appointment_number(self):
        """Generate unique appointment number: APT-YYYYMMDD-XXXX"""
        date_str = timezone.now().strftime('%Y%m%d')
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        return f"APT-{date_str}-{random_str}"

    def generate_video_room(self):
        """
        Generate a Whereby room and persist both guest and host URLs.

        Requires settings.WHEREBY_API_KEY.
        """
        import requests
        from urllib.parse import urlparse
        from datetime import timedelta

        if not getattr(settings, "WHEREBY_API_KEY", None):
            raise ValueError("WHEREBY_API_KEY is not configured in settings.")

        headers = {
            "Authorization": f"Bearer {settings.WHEREBY_API_KEY}",
            "Content-Type": "application/json",
        }

        # Whereby requires an endDate; we set it relative to appointment time
        end_date = self.date + timedelta(days=1)
        data = {
            "endDate": end_date.isoformat(),
            "fields": ["hostRoomUrl"],
        }

        response = requests.post(
            "https://api.whereby.dev/v1/meetings",
            json=data,
            headers=headers,
            timeout=20,
        )
        response.raise_for_status()
        room_data = response.json()

        self.video_room_url = room_data.get("roomUrl", "") or ""
        self.video_host_url = room_data.get("hostRoomUrl", "") or ""

        # Derive a stable-ish id from the room URL for admin/debug
        if self.video_room_url:
            self.video_room_id = urlparse(self.video_room_url).path.strip("/").split("/")[-1]

    @property
    def can_cancel(self):
        """Check if appointment can be cancelled (at least 2 hours before)"""
        if self.status in ['cancelled', 'completed', 'no_show']:
            return False
        
        from datetime import datetime, timedelta
        appointment_datetime = datetime.combine(self.date, self.start_time)
        now = datetime.now()
        
        return appointment_datetime > now + timedelta(hours=2)

    @property
    def can_reschedule(self):
        """Check if appointment can be rescheduled (max 2 times, at least 2 hours before)"""
        if self.reschedule_count >= 2:
            return False
        return self.can_cancel

    @property
    def can_join(self):
        """Check if video room can be joined (15 min before to 30 min after start)"""
        if self.status not in ['confirmed', 'in_progress']:
            return False
        
        from datetime import datetime, timedelta
        appointment_datetime = datetime.combine(self.date, self.start_time)
        appointment_end = datetime.combine(self.date, self.end_time)
        now = datetime.now()
        
        join_start = appointment_datetime - timedelta(minutes=15)
        join_end = appointment_end + timedelta(minutes=30)
        
        return join_start <= now <= join_end