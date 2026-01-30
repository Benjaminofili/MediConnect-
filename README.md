# MediConnect - Telemedicine Backend Platform

A comprehensive telemedicine backend API built with Django and Django REST Framework.

## Features

### User Authentication
- Patient and Doctor registration
- JWT-based authentication
- Email verification
- Password reset

### Doctor Management
- Doctor profiles with specializations
- Availability scheduling
- Search and filtering
- Verification system

### Appointment System
- Real-time slot availability
- Booking management
- Cancellation and rescheduling
- Automated reminders

### Medical Records
- Patient health profiles
- Consultation history
- Prescription management
- Document uploads

### Video Consultations
- Jitsi Meet integration
- Secure video rooms
- Session management

## Tech Stack

| Component | Technology |
|-----------|------------|
| Framework | Django 4.2+ |
| API | Django REST Framework |
| Authentication | JWT (Simple JWT) |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Video | Jitsi Meet |
| Email | SMTP / Console |

## Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Git
- Virtual environment (recommended)

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/Benjaminofili/MediConnect.git
cd MediConnect
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the root directory (use `.env.example` as a template):
```bash
cp .env.example .env
```

### 5. Run Migrations
```bash
python manage.py migrate
```

### 6. Create Superuser
```bash
python manage.py createsuperuser
```

### 7. Run Development Server
```bash
python manage.py runserver
```

## Project Structure

```
telemedicine/
├── accounts/                  # User authentication
├── appointments/              # Booking system
├── config/                    # Django settings
├── consultations/             # Video sessions
├── dashboard/                 # Dashboard views
├── doctors/                   # Doctor management
├── landing/                   # Landing pages
├── notifications/             # Email system
├── records/                   # Medical records
├── templates/                 # HTML templates
├── static/                    # Static files
├── media/                     # Uploaded files
├── tests/                     # Test files
├── scripts/                   # Utility scripts
├── manage.py                  # Django management
└── requirements.txt           # Dependencies
```

## API Documentation

API documentation is available at:
- Swagger UI: http://localhost:8000/api/docs/
- ReDoc: http://localhost:8000/api/redoc/

## Running Tests

```bash
pytest
```

## License

This project is licensed under the MIT License.