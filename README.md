# MediConnect

A Django REST API for remote medical consultations. Patients book appointments with doctors, join video consultations (Whereby), and receive prescriptions and medical records — all authenticated with JWT and backed by PostgreSQL.

## What it does
- Patients and doctors register and authenticate separately, with role-based profiles.
- Patients browse doctors by specialization and book from their published availability.
- Appointments move through a booking → video consultation → prescription lifecycle, each with its own API endpoints.
- Consultations are conducted over Whereby video rooms created per appointment.
- Patients' medical history and uploaded documents are stored in Supabase (S3-compatible) object storage.

## Modules & Features
- **Accounts Module:** Support for Patients, Doctors, and Administrators with JWT and session-based authentication.
- **Doctors Module:** Profile management, specialization categorization, and availability scheduling.
- **Appointments Module:** Booking system, status tracking, and notification triggers.
- **Consultations Module:** Video call integration (Whereby), notes, and prescription generation.
- **Medical Records Module:** Secure upload, storage (Supabase S3), and categorization of medical documents.
- **Dashboard:** Personalized views for patients (records, upcoming appointments) and doctors (schedule, patient list).
- **Landing Page:** Public-facing platform introduction and doctor directory.

## Technology Stack
- **Backend:** Django, Django REST Framework
- **Database:** PostgreSQL
- **Video Integration:** Whereby API
- **Storage:** Supabase Object Storage (S3 compatible)
- **Testing:** Pytest

## Installation Guide

### Prerequisites
- Python 3.10 or higher
- pip
- Git
- Virtual environment tool (`venv`)

### Setup Steps

1. **Clone the Repository**
   ```bash
   git clone https://github.com/Benjaminofili/MediConnect-.git
   cd MediConnect-
   ```

2. **Create and Activate Virtual Environment**
   *Windows:*
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate
   ```
   *Linux/macOS:*
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   Create a `.env` file in the project root directory with the following variables:
   ```ini
   SECRET_KEY=your-super-secret-key-here
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   
   # Database (leave empty for SQLite)
   DATABASE_URL=
   
   # Whereby Video Integration
   WHEREBY_API_KEY=your-whereby-api-key
   
   # Supabase Storage (optional)
   USE_SPACES=False
   SUPABASE_ACCESS_KEY_ID=
   SUPABASE_SECRET_ACCESS_KEY=
   SUPABASE_STORAGE_BUCKET_NAME=
   SUPABASE_S3_ENDPOINT_URL=
   SUPABASE_PROJECT_REF=

   # Email (SMTP, e.g. Gmail app password)
   EMAIL_BACKEND=smtp
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=465
   EMAIL_USE_SSL=True
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=your-app-password-here
   DEFAULT_FROM_EMAIL=MediConnect <your-email@gmail.com>
   ```
   See [.env.example](.env.example) for the full list, including SendGrid/Mailgun alternatives.

5. **Database Setup**
   ```bash
   python manage.py migrate
   ```

6. **Create Superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run Development Server**
   ```bash
   python manage.py runserver
   ```
   Access the application at `http://127.0.0.1:8000`.

## Testing

The project uses `pytest` for testing. The test suite includes integration tests for the real API as well as mocked tests.

### Running Tests

To run the standard test suite (using mocks):
```bash
pytest
```

### Real API Tests
Some tests interact with the real Whereby API. These are marked with `@pytest.mark.real_api` or can be enabled globally via environment variables.

To run tests including real API calls:
```bash
# Option 1: Use the marker
pytest -m real_api

# Option 2: Enable via environment variable
$env:REAL_API_TESTS="true"; pytest
```

### Test Structure
Tests are located in the `tests/` directory:
- `tests/integration/`: Contains integration flows for Auth, Booking, Consultations, etc.
- `conftest.py`: Global fixtures including API clients, user factories, and mocks.
- `pytest.ini`: Configuration for pytest.

## API Documentation
The platform provides a RESTful API, authenticated with JWT (`djangorestframework-simplejwt`). Base URL: `http://localhost:8000/api/`.

| Area | Endpoints |
|---|---|
| Auth | `POST /api/auth/register/patient/`, `POST /api/auth/register/doctor/`, `POST /api/auth/login/`, `POST /api/auth/logout/`, `POST /api/auth/token/refresh/`, `GET /api/auth/me/` |
| Doctors | `GET /api/doctors/`, `GET /api/doctors/{id}/`, `GET /api/doctors/{id}/slots/`, `GET /api/doctors/specializations/` |
| Appointments | `POST /api/appointments/book/`, `GET /api/appointments/`, `GET /api/appointments/upcoming/`, `POST /api/appointments/{id}/cancel/`, `POST /api/appointments/{id}/reschedule/`, `POST /api/appointments/{id}/join/` |
| Consultations | `GET /api/consultations/`, `GET /api/consultations/{appointment_id}/`, `POST /api/consultations/{appointment_id}/start/`, `POST /api/consultations/{appointment_id}/end/`, `POST /api/consultations/{appointment_id}/prescription/` |
| Records | `GET /api/records/profile/`, `GET /api/records/history/`, `POST /api/records/documents/upload/` |

Send `Authorization: Bearer <access_token>` (from `/api/auth/login/`) on authenticated requests. See `accounts/urls.py`, `doctors/urls.py`, `appointments/urls.py`, `consultations/urls.py`, and `records/urls.py` for the complete route list.

### Example flow: booking to prescription

```bash
# 1. Log in as a patient
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "patient@example.com", "password": "your-password"}'
# -> {"access": "<jwt>", "refresh": "<jwt>", "user": {"id": 1, "email": "...", "user_type": "patient"}}

# 2. Book an appointment with a doctor's open time slot
curl -X POST http://localhost:8000/api/appointments/book/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"doctor_id": 3, "time_slot_id": 42, "reason": "Persistent cough"}'
# -> {"id": 17, "status": "confirmed", "doctor": 3, "patient": 1, ...}

# 3. Join the video consultation (creates the Whereby room on first call)
curl -X GET http://localhost:8000/api/appointments/17/join/ \
  -H "Authorization: Bearer <access_token>"
# -> {"video_room_url": "https://mediconnect.whereby.com/..."}

# 4. Doctor issues a prescription after the consultation
curl -X POST http://localhost:8000/api/consultations/17/prescription/ \
  -H "Authorization: Bearer <doctor_access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "diagnosis": "Acute bronchitis",
    "items": [
      {"medicine_name": "Amoxicillin 500mg", "dosage": "1 tablet", "frequency": "three_times_daily", "duration": "7_days"}
    ]
  }'
# -> {"message": "Prescription created successfully", "prescription": {"id": 5, "prescription_number": "...", "diagnosis": "Acute bronchitis", "items": [...]}}
```
