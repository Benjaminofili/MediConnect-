# create_test_pdf.py
# Run: pip install reportlab && python create_test_pdf.py

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from datetime import datetime
import os

os.makedirs('test_documents', exist_ok=True)

def create_lab_report():
    filename = 'test_documents/blood_test_report.pdf'
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    # Header
    c.setFont("Helvetica-Bold", 20)
    c.drawString(1*inch, height - 1*inch, "MEDICAL LAB REPORT")
    
    c.setFont("Helvetica", 12)
    c.drawString(1*inch, height - 1.5*inch, f"Date: {datetime.now().strftime('%B %d, %Y')}")
    c.drawString(1*inch, height - 1.8*inch, "Patient ID: TEST-001")
    c.drawString(1*inch, height - 2.1*inch, "Patient Name: Test Patient")
    
    # Line
    c.line(1*inch, height - 2.3*inch, width - 1*inch, height - 2.3*inch)
    
    # Results
    c.setFont("Helvetica-Bold", 14)
    c.drawString(1*inch, height - 2.7*inch, "Blood Test Results:")
    
    c.setFont("Helvetica", 12)
    results = [
        ("Hemoglobin", "14.5 g/dL", "Normal (13.5-17.5)"),
        ("White Blood Cells", "7,500 /μL", "Normal (4,500-11,000)"),
        ("Platelets", "250,000 /μL", "Normal (150,000-400,000)"),
        ("Blood Sugar (Fasting)", "92 mg/dL", "Normal (70-100)"),
        ("Cholesterol (Total)", "185 mg/dL", "Normal (<200)"),
        ("Creatinine", "1.0 mg/dL", "Normal (0.7-1.3)"),
    ]
    
    y = height - 3.2*inch
    for test, value, reference in results:
        c.drawString(1*inch, y, test)
        c.drawString(3.5*inch, y, value)
        c.drawString(5*inch, y, reference)
        y -= 0.3*inch
    
    # Footer
    c.line(1*inch, 2*inch, width - 1*inch, 2*inch)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(1*inch, 1.6*inch, "Verified by: Dr. John Smith, MD")
    c.drawString(1*inch, 1.3*inch, "Laboratory: City Medical Center")
    
    c.save()
    print(f"✅ Created: {filename}")

def create_prescription():
    filename = 'test_documents/prescription.pdf'
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    # Header
    c.setFont("Helvetica-Bold", 24)
    c.drawString(1*inch, height - 1*inch, "℞ PRESCRIPTION")
    
    c.setFont("Helvetica", 12)
    c.drawString(1*inch, height - 1.5*inch, f"Date: {datetime.now().strftime('%B %d, %Y')}")
    c.drawString(1*inch, height - 1.8*inch, "Patient: Test Patient")
    c.drawString(1*inch, height - 2.1*inch, "Age: 35 years")
    
    c.line(1*inch, height - 2.3*inch, width - 1*inch, height - 2.3*inch)
    
    # Medications
    c.setFont("Helvetica-Bold", 14)
    c.drawString(1*inch, height - 2.7*inch, "Medications:")
    
    c.setFont("Helvetica", 12)
    medications = [
        "1. Amoxicillin 500mg - Take 1 capsule 3 times daily for 7 days",
        "2. Paracetamol 500mg - Take 1 tablet every 6 hours as needed",
        "3. Vitamin C 1000mg - Take 1 tablet daily",
        "4. Probiotics - Take 1 capsule daily with meals",
    ]
    
    y = height - 3.2*inch
    for med in medications:
        c.drawString(1*inch, y, med)
        y -= 0.4*inch
    
    # Instructions
    c.setFont("Helvetica-Bold", 12)
    c.drawString(1*inch, y - 0.3*inch, "Instructions:")
    c.setFont("Helvetica", 11)
    c.drawString(1*inch, y - 0.6*inch, "- Complete the full course of antibiotics")
    c.drawString(1*inch, y - 0.9*inch, "- Drink plenty of fluids")
    c.drawString(1*inch, y - 1.2*inch, "- Follow up in 1 week if symptoms persist")
    
    # Signature
    c.line(1*inch, 2*inch, width - 1*inch, 2*inch)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(1*inch, 1.6*inch, "Dr. Sarah Johnson, MD")
    c.drawString(1*inch, 1.3*inch, "License No: MED-12345")
    
    c.save()
    print(f"✅ Created: {filename}")

def create_xray_report():
    filename = 'test_documents/chest_xray_report.pdf'
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    c.setFont("Helvetica-Bold", 20)
    c.drawString(1*inch, height - 1*inch, "RADIOLOGY REPORT")
    
    c.setFont("Helvetica", 12)
    c.drawString(1*inch, height - 1.5*inch, f"Date: {datetime.now().strftime('%B %d, %Y')}")
    c.drawString(1*inch, height - 1.8*inch, "Patient: Test Patient")
    c.drawString(1*inch, height - 2.1*inch, "Exam: Chest X-Ray (PA View)")
    
    c.line(1*inch, height - 2.3*inch, width - 1*inch, height - 2.3*inch)
    
    c.setFont("Helvetica-Bold", 14)
    c.drawString(1*inch, height - 2.7*inch, "Findings:")
    
    c.setFont("Helvetica", 12)
    findings = [
        "- Heart size is within normal limits",
        "- Lungs are clear bilaterally",
        "- No pleural effusion identified",
        "- Bony structures appear intact",
        "- No acute cardiopulmonary abnormality",
    ]
    
    y = height - 3.2*inch
    for finding in findings:
        c.drawString(1*inch, y, finding)
        y -= 0.3*inch
    
    c.setFont("Helvetica-Bold", 14)
    c.drawString(1*inch, y - 0.3*inch, "Impression:")
    c.setFont("Helvetica", 12)
    c.drawString(1*inch, y - 0.6*inch, "Normal chest X-ray. No acute findings.")
    
    c.line(1*inch, 2*inch, width - 1*inch, 2*inch)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(1*inch, 1.6*inch, "Radiologist: Dr. Michael Chen, MD")
    
    c.save()
    print(f"✅ Created: {filename}")

# Create all documents
create_lab_report()
create_prescription()
create_xray_report()

print("\n📁 All test documents created in 'test_documents' folder!")