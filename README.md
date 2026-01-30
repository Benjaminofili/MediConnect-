# MediConnect - Telemedicine Backend Platform

A comprehensive telemedicine backend API built with Django and Django REST Framework.

---

## Features

- **User Authentication**
  - Patient and Doctor registration
  - JWT-based authentication
  - Email verification
  - Password reset

- **Doctor Management**
  - Doctor profiles with specializations
  - Availability scheduling
  - Search and filtering
  - Verification system

- **Appointment System**
  - Real-time slot availability
  - Booking management
  - Cancellation and rescheduling
  - Automated reminders

- **Medical Records**
  - Patient health profiles
  - Consultation history
  - Prescription management
  - Document uploads

- **Video Consultations**
  - Jitsi Meet integration
  - Secure video rooms
  - Session management

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Framework | Django 4.2 |
| API | Django REST Framework |
| Authentication | JWT (Simple JWT) |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Video | Jitsi Meet |
| Email | SMTP / Console |

---

## Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Git
- Virtual environment (recommended)

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/benjaminofili/telemedicine.git
```
cd telemedicine

2. Create Virtual Environment
Bash
```
python -m venv venv
```
3. Activate Virtual Environment
Windows (PowerShell):

PowerShell
```
.\venv\Scripts\Activate.ps1
```
macOS/Linux:

Bash

source venv/bin/activate
4. Install Dependencies
Bash
```
pip install -r requirements.txt
```

5. Configure Environment Variables
Bash
```
cp .env.example .env
# Edit .env with your settings
```

6. Run Migrations
Bash
```
cd src
python manage.py migrate
```

7. Create Superuser
Bash
```
python manage.py createsuperuser
```
8. Run Development Server
Bash
```
python manage.py runserver
```
## Project Structure

```
telemedicine/
├── docs/                      # Documentation
│   ├── progress/             # Progress tracking
│   ├── setup/                # Setup guides
│   └── pdf/                  # PDF documentation
├── scripts/                   # Utility scripts
│   ├── test_email.py         # Email testing
│   ├── test_email_validator.py  # Email validation tests
│   ├── seed_data.py          # Database seeding
│   └── ...
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
├── manage.py                  # Django management
└── requirements.txt           # Dependencies
```
API Documentation
API documentation is available at:

Swagger UI: http://localhost:8000/api/docs/
ReDoc: http://localhost:8000/api/redoc/
Running Tests
Bash

cd src
pytest
With coverage:

Bash

pytest --cov=apps --cov-report=html
Code Quality
Format Code
Bash

black src/
isort src/
Lint Code
Bash

flake8 src/
Environment Variables
Variable	Description	Default
DEBUG	Debug mode	True
SECRET_KEY	Django secret key	-
DATABASE_URL	Database connection	sqlite:///db.sqlite3
EMAIL_BACKEND	Email backend	console
JWT_ACCESS_TOKEN_LIFETIME	Token lifetime (min)	60
JITSI_DOMAIN	Video service domain	meet.jit.si
Contributing
Fork the repository
Create a feature branch (git checkout -b feature/amazing-feature)
Commit changes (git commit -m 'Add amazing feature')
Push to branch (git push origin feature/amazing-feature)
Open a Pull Request
License
This project is licensed under the MIT License.

Contact
Your Name - your.email@example.com

Project Link: https://github.com/yourusername/telemedicine