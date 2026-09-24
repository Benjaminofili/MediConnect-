# Telemedicine Platform

A Web-Based Healthcare Consultation System designed to facilitate remote medical consultations between patients and healthcare providers. The system aims to bridge the gap between patients and doctors by leveraging modern web technologies to provide a seamless virtual healthcare experience.

## Project Objectives
- **Accessibility:** Enable patients to consult doctors from anywhere.
- **Efficiency:** Streamline appointment booking and management.
- **Security:** Ensure patient data privacy and security.
- **Usability:** Provide intuitive interfaces for all users.
- **Scalability:** Build a system that can grow with demand.

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

## System Architecture
The platform follows a three-tier architecture with separate guides for Patients, Doctors, and Administrators. 

## Installation Guide

### Prerequisites
- Python 3.10 or higher
- pip
- Git
- Virtual environment tool (`venv`)

### Setup Steps

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/telemedicine.git
   cd telemedicine
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
