# records/forms.py

from django import forms
from .models import HealthProfile, MedicalHistory, MedicalDocument


class HealthProfileForm(forms.ModelForm):
    """Form for patient health profile"""
    
    class Meta:
        model = HealthProfile
        exclude = ['patient', 'created_at', 'updated_at']
        widgets = {
            'height_cm': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Height in cm',
                'step': '0.01'
            }),
            'weight_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Weight in kg',
                'step': '0.01'
            }),
            'blood_type': forms.Select(attrs={'class': 'form-select'}),
            'allergies': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'List any allergies (e.g., Penicillin, Peanuts)'
            }),
            'chronic_conditions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'List chronic conditions (e.g., Diabetes, Hypertension)'
            }),
            'current_medications': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'List current medications'
            }),
            'past_surgeries': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'List past surgeries with dates'
            }),
            'family_history': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Family medical history'
            }),
            'smoking_status': forms.Select(attrs={'class': 'form-select'}),
            'alcohol_consumption': forms.Select(attrs={'class': 'form-select'}),
            'exercise_frequency': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 3 times per week'
            }),
            'emergency_contact_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Emergency contact name'
            }),
            'emergency_contact_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Emergency contact phone'
            }),
            'emergency_contact_relationship': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Spouse, Parent'
            }),
            'insurance_provider': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Insurance provider name'
            }),
            'insurance_policy_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Policy number'
            }),
        }


class MedicalHistoryForm(forms.ModelForm):
    """Form for adding medical history events"""
    
    class Meta:
        model = MedicalHistory
        exclude = ['patient', 'created_at', 'updated_at']
        widgets = {
            'event_type': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Appendectomy, COVID-19 Vaccination'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe the event'
            }),
            'event_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'doctor_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Doctor name (optional)'
            }),
            'hospital_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Hospital/Clinic name (optional)'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Additional notes'
            }),
        }


class MedicalDocumentForm(forms.ModelForm):
    """Form for uploading medical documents"""
    
    class Meta:
        model = MedicalDocument
        fields = ['title', 'document_type', 'file', 'description', 'document_date']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Blood Test Results - January 2024'
            }),
            'document_type': forms.Select(attrs={'class': 'form-select'}),
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png,.doc,.docx'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Brief description (optional)'
            }),
            'document_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Max 10MB
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError('File size must be under 10MB.')
            
            # Check extension
            allowed_extensions = ['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx']
            ext = file.name.split('.')[-1].lower()
            if ext not in allowed_extensions:
                raise forms.ValidationError(
                    f'Allowed file types: {", ".join(allowed_extensions)}'
                )
        return file