# dashboard/urls.py

from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
     # AUTH URLS (Public)
    path('login/', views.login_page, name='login'),
    path('register/', views.register_page, name='register_choice'),
    path('register/doctor/', views.register_doctor_page, name='register_doctor'),
    path('register/patient/', views.register_patient_page, name='register_patient'),
    path('logout/', views.logout_page, name='logout'),

     # Email Verification
    path('verification-sent/', views.verification_sent_page, name='verification_sent'),
    path('verify-email/<uidb64>/<token>/', views.verify_email, name='verify_email'),
    path('resend-verification/', views.resend_verification, name='resend_verification'),
    
    # Password Reset
    path('forgot-password/', views.forgot_password_page, name='forgot_password'),
    path('reset-password/<uidb64>/<token>/', views.reset_password_page, name='reset_password'),

    # Doctor URLs
    path('doctor/dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    # Appointments
    path('doctor/appointments/', views.doctor_appointments, name='doctor_appointments'),
    path('doctor/appointments/create/', views.doctor_create_appointment, name='doctor_create_appointment'),
    path('doctor/appointments/calendar/', views.doctor_appointment_calendar, name='doctor_appointment_calendar'),
    path('doctor/appointments/<int:pk>/', views.doctor_appointment_detail, name='doctor_appointment_detail'),
    path('doctor/appointments/<int:pk>/cancel/', views.doctor_cancel_appointment, name='doctor_cancel_appointment'),
    path('doctor/appointments/calendar/events/',views.doctor_appointment_events,name='doctor_appointment_events'),
    # Doctor appointment management
    path('doctor/appointments/pending/', views.doctor_pending_appointments, name='doctor_pending_appointments'),
    path('doctor/appointments/<int:pk>/confirm/', views.doctor_confirm_appointment, name='doctor_confirm_appointment'),
    
    
    # Patients
    path('doctor/patients/', views.doctor_patients, name='doctor_patients'),
    path('doctor/patient/<int:pk>/', views.doctor_patient_detail, name='doctor_patient_detail'),
    path('doctor/patient/<int:pk>/records/', views.doctor_patient_records, name='doctor_patient_records'),
    path('doctor/patient/<int:patient_id>/document/<int:doc_id>/', views.doctor_patient_document_view, name='doctor_patient_document_view'),
   
    # Prescriptions
    path('doctor/prescriptions/', views.doctor_prescriptions, name='doctor_prescriptions'),
    path('doctor/prescriptions/export/<str:format>/', views.doctor_prescriptions_export, name='doctor_prescriptions_export'),
    path('doctor/prescriptions/<int:pk>/', views.doctor_prescription_detail, name='doctor_prescription_detail'),
    path('doctor/prescription/create/<int:patient_id>/',views.doctor_prescription_create, name='doctor_prescription_create'),
    # Profile
    path('doctor/profile/', views.doctor_profile, name='doctor_profile'),
    path('doctor/change-password/', views.doctor_change_password, name='doctor_change_password'),
    path('doctor/notifications/', views.doctor_notifications, name='doctor_notifications'),
    # 
    # Consultations
    path('doctor/consultations/', views.consultations_list, name='consultations_list'),

#     # Patient URLs
    path('patient/dashboard/', views.patient_dashboard, name='patient_dashboard'),
     # Appointments
    path('patient/appointments/', views.patient_appointments, name='patient_appointments'),
    path('patient/appointments/calendar/', views.patient_appointment_calendar, name='patient_appointment_calendar'),
    path('patient/appointments/events/', views.patient_appointment_events, name='patient_appointment_events'),
    path('patient/appointments/create/', views.patient_create_appointment, name='patient_create_appointment'),
    path('patient/appointments/<int:pk>/', views.patient_appointment_detail, name='patient_appointment_detail'),
    path('patient/appointments/<int:pk>/cancel/', views.patient_cancel_appointment, name='patient_cancel_appointment'),
    
    # Doctors
    path('patient/doctors/', views.patient_doctors, name='patient_doctors'),
    path('patient/doctors/<int:pk>/', views.patient_doctor_detail, name='patient_doctor_detail'),
    
    # Prescriptions
    path('patient/prescriptions/', views.patient_prescriptions, name='patient_prescriptions'),
    path('patient/prescriptions/export/<str:format>/', views.patient_prescriptions_export, name='patient_prescriptions_export'),
    path('patient/prescriptions/<int:pk>/', views.patient_prescription_detail, name='patient_prescription_detail'),
    path('patient/prescriptions/<int:pk>/download/', views.patient_prescription_download, name='patient_prescription_download'),
    
    # Profile
    path('patient/profile/', views.patient_profile, name='patient_profile'),
    path('patient/change-password/', views.patient_change_password, name='patient_change_password'),
    path('patient/notifications/', views.patient_notifications, name='patient_notifications'),
    
    # Patient Records
    path('patient/health-profile/', views.patient_health_profile, name='patient_health_profile'),
    path('patient/medical-history/', views.patient_medical_history, name='patient_medical_history'),
    path('patient/medical-history/<int:pk>/delete/', views.patient_medical_history_delete, name='patient_medical_history_delete'),
    path('patient/documents/', views.patient_medical_documents, name='patient_medical_documents'),
    path('patient/documents/<int:pk>/download/', views.patient_document_download, name='patient_document_download'),
    path('patient/documents/<int:pk>/delete/', views.patient_document_delete, name='patient_document_delete'),

#     # Shared URLs
    path('encounter/<int:appointment_id>/', views.active_encounter, name='active_encounter'),
    
    # Endpoint to handle "Complete Appointment"
    # Encounter URLs
    path('encounter/<int:appointment_id>/', views.active_encounter, name='active_encounter'),
    path('encounter/<int:appointment_id>/save-draft/', views.save_encounter_draft, name='save_encounter_draft'),
    path('encounter/<int:appointment_id>/end/', views.end_encounter, name='end_encounter'),
    path('encounter/<int:appointment_id>/leave/', views.leave_encounter, name='leave_encounter'),
    path('consultations/', views.consultations_list, name='consultations'),
    path('chat/', views.chat, name='chat'),
    path('video-call/', views.video_call, name='video_call'),
    path('voice-call/', views.voice_call, name='voice_call'),
    
]