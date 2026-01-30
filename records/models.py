import os
from django.conf import settings
from django.db import models
from storages.backends.s3boto3 import S3Boto3Storage

# Define a private storage backend for medical documents
class PrivateMediaStorage(S3Boto3Storage):
    """
    Private storage backend for medical documents with Supabase S3 configuration.
    Uses the same Supabase credentials as the default storage but with a private bucket.
    S3Boto3Storage automatically reads AWS_* settings from Django settings.
    """
    location = ''
    default_acl = 'private'
    file_overwrite = False
    custom_domain = False  # Forces signed URLs   
    bucket_name = os.getenv('SUPABASE_PRIVATE_BUCKET_NAME', 'medical-records')
    
    # S3Boto3Storage will automatically use these from Django settings:
    # - AWS_ACCESS_KEY_ID (set to SUPABASE_ACCESS_KEY_ID in settings.py)
    # - AWS_SECRET_ACCESS_KEY (set to SUPABASE_SECRET_ACCESS_KEY in settings.py)
    # - AWS_S3_ENDPOINT_URL (set to SUPABASE_S3_ENDPOINT_URL in settings.py)
    # - AWS_S3_REGION_NAME (set to SUPABASE_REGION in settings.py)

class HealthProfile(models.Model):
    """Patient's health profile with medical information."""
    
    BLOOD_TYPE_CHOICES = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('O+', 'O+'), ('O-', 'O-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('unknown', 'Unknown'),
    ]
    
    SMOKING_CHOICES = [
        ('never', 'Never'),
        ('former', 'Former Smoker'),
        ('current', 'Current Smoker'),
    ]
    
    ALCOHOL_CHOICES = [
        ('none', 'None'),
        ('occasional', 'Occasional'),
        ('moderate', 'Moderate'),
        ('heavy', 'Heavy'),
    ]
    
    patient = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='health_profile'
    )
    
    # Physical info
    blood_type = models.CharField(max_length=10, choices=BLOOD_TYPE_CHOICES, default='unknown')
    height_cm = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Medical history
    allergies = models.TextField(blank=True, help_text="List all known allergies")
    chronic_conditions = models.TextField(blank=True, help_text="Diabetes, hypertension, etc.")
    current_medications = models.TextField(blank=True, help_text="Currently taking medications")
    past_surgeries = models.TextField(blank=True, help_text="List of past surgeries")
    family_history = models.TextField(blank=True, help_text="Family medical history")
    
    # Lifestyle
    smoking_status = models.CharField(max_length=10, choices=SMOKING_CHOICES, default='never')
    alcohol_consumption = models.CharField(max_length=10, choices=ALCOHOL_CHOICES, default='none')
    exercise_frequency = models.CharField(max_length=100, blank=True, help_text="How often do you exercise?")
    
    # Emergency contact
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    emergency_contact_relationship = models.CharField(max_length=50, blank=True)
    
    # Insurance
    insurance_provider = models.CharField(max_length=100, blank=True)
    insurance_policy_number = models.CharField(max_length=50, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Health Profile: {self.patient.email}"
    
    @property
    def bmi(self):
        """Calculate BMI if height and weight are available."""
        if self.height_cm and self.weight_kg and self.height_cm > 0:
            height_m = float(self.height_cm) / 100
            return round(float(self.weight_kg) / (height_m ** 2), 2)
        return None


class MedicalHistory(models.Model):
    """Record of past medical events."""
    
    EVENT_TYPES = [
        ('diagnosis', 'Diagnosis'),
        ('surgery', 'Surgery'),
        ('hospitalization', 'Hospitalization'),
        ('vaccination', 'Vaccination'),
        ('injury', 'Injury'),
        ('other', 'Other'),
    ]
    
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='medical_history'
    )
    
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    event_date = models.DateField()
    doctor_name = models.CharField(max_length=100, blank=True)
    hospital_name = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-event_date']
        verbose_name_plural = "Medical histories"
    
    def __str__(self):
        return f"{self.title} - {self.patient.email}"


class MedicalDocument(models.Model):
    """Medical documents uploaded by patients."""
    
    DOCUMENT_TYPES = [
        ('lab_report', 'Lab Report'),
        ('prescription', 'Prescription'),
        ('xray', 'X-Ray'),
        ('mri', 'MRI Scan'),
        ('ct_scan', 'CT Scan'),
        ('ultrasound', 'Ultrasound'),
        ('ecg', 'ECG/EKG'),
        ('blood_test', 'Blood Test'),
        ('vaccination', 'Vaccination Record'),
        ('insurance', 'Insurance Document'),
        ('referral', 'Referral Letter'),
        ('discharge', 'Discharge Summary'),
        ('other', 'Other'),
    ]
    
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='medical_documents'
    )
    
    title = models.CharField(max_length=200)
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    file = models.FileField(upload_to='documents/%Y/%m/', storage=PrivateMediaStorage())
    file_size = models.PositiveIntegerField(default=0, help_text="File size in bytes")
    description = models.TextField(blank=True)
    
    # Optional link to consultation
    consultation = models.ForeignKey(
        'consultations.Consultation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents'
    )
    
    # Date on the document (e.g., when lab test was done)
    document_date = models.DateField(null=True, blank=True)
    
    # Timestamps
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.title} - {self.patient.email}"
    
    def save(self, *args, **kwargs):
        # Get file size from the uploaded file object before saving
        # This works for both new uploads and existing files
        if self.file:
            # If file is a new upload (has a file object), get size from it
            if hasattr(self.file, 'size') and self.file.size:
                self.file_size = self.file.size
            # If file is already saved (has a name), try to get size from storage
            elif hasattr(self.file, 'storage') and hasattr(self.file, 'name') and self.file.name:
                try:
                    # For S3 storage, we need to get the size from the storage backend
                    if hasattr(self.file.storage, 'size'):
                        self.file_size = self.file.storage.size(self.file.name)
                    else:
                        # Fallback: try to open and get size
                        with self.file.open('rb') as f:
                            f.seek(0, 2)  # Seek to end
                            self.file_size = f.tell()
                except Exception:
                    # If we can't get size, keep existing value or default to 0
                    if not self.file_size:
                        self.file_size = 0
        super().save(*args, **kwargs)
    
    @property
    def file_size_display(self):
        """Convert bytes to human readable format."""
        size = self.file_size
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size / (1024 * 1024):.1f} MB"


     