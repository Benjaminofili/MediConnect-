# Scripts

This directory contains utility scripts for development, testing, and maintenance.

## Email Testing

### `test_email.py`
Test email configuration and send test emails.

**Usage:**
```bash
python scripts/test_email.py recipient@example.com
```

**Features:**
- Displays current email configuration
- Sends test email to verify SMTP setup
- Provides helpful debugging information

### `test_email_validator.py`
Test the email validation system.

**Usage:**
```bash
python scripts/test_email_validator.py
```

**Features:**
- Tests email format validation
- Tests disposable email detection
- Tests typo suggestion system
- Comprehensive test suite with 18+ test cases

## Data Management

### `seed_data.py`
Seed the database with test data for development.

**Usage:**
```bash
python scripts/seed_data.py
```

## Documentation

### `create_test_pdf.py`
Generate test PDF documents for testing the PDF generation system.

**Usage:**
```bash
python scripts/create_test_pdf.py
```

### `map.py`
Generate project structure map (Python version).

**Usage:**
```bash
python scripts/map.py
```

### `Map-ProjectStructure.ps1`
Generate project structure map (PowerShell version).

**Usage:**
```powershell
.\scripts\Map-ProjectStructure.ps1
```

## Running Scripts

All scripts should be run from the project root directory:

```bash
# From project root
cd telemedicine/

# Run a script
python scripts/script_name.py
```

**Note:** Make sure your virtual environment is activated before running scripts:

```bash
# Windows
.\venv\Scripts\Activate.ps1

# Linux/Mac
source venv/bin/activate
```
