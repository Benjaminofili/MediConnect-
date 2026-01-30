"""
Test email validation functionality.
Run this to test the email validator.

Usage:
    python test_email_validator.py
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from accounts.email_validator import EmailValidator


def test_email_validation():
    """Test various email validation scenarios."""
    
    print("=" * 70)
    print("Email Validator Test Suite")
    print("=" * 70)
    
    test_cases = [
        # (email, should_pass, description)
        ("user@gmail.com", True, "Valid Gmail address"),
        ("test.user+tag@outlook.com", True, "Valid Outlook with plus addressing"),
        ("doctor@hospital.edu", True, "Valid .edu domain"),
        
        # Invalid formats
        ("notanemail", False, "Missing @ symbol"),
        ("@gmail.com", False, "Missing local part"),
        ("user@", False, "Missing domain"),
        ("user @gmail.com", False, "Space in email"),
        
        # Disposable emails
        ("test@10minutemail.com", False, "Disposable: 10minutemail"),
        ("user@guerrillamail.com", False, "Disposable: guerrillamail"),
        ("temp@mailinator.com", False, "Disposable: mailinator"),
        ("fake@tempmail.com", False, "Disposable: tempmail"),
        ("throwaway@yopmail.com", False, "Disposable: yopmail"),
        
        # Typos
        ("user@gmai.com", False, "Typo: gmai.com → gmail.com"),
        ("user@gmial.com", False, "Typo: gmial.com → gmail.com"),
        ("user@yahooo.com", False, "Typo: yahooo.com → yahoo.com"),
        ("user@hotmial.com", False, "Typo: hotmial.com → hotmail.com"),
    ]
    
    passed = 0
    failed = 0
    
    for email, should_pass, description in test_cases:
        is_valid, error_msg, suggestion = EmailValidator.validate_email(email)
        
        # Determine if test passed
        test_passed = (is_valid == should_pass)
        
        if test_passed:
            status = "✅ PASS"
            passed += 1
        else:
            status = "❌ FAIL"
            failed += 1
        
        print(f"\n{status} | {description}")
        print(f"  Email: {email}")
        print(f"  Expected: {'Valid' if should_pass else 'Invalid'}")
        print(f"  Got: {'Valid' if is_valid else 'Invalid'}")
        
        if error_msg:
            print(f"  Error: {error_msg}")
        if suggestion:
            print(f"  Suggestion: {suggestion}")
    
    print("\n" + "=" * 70)
    print(f"Results: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print("=" * 70)
    
    return failed == 0


def test_specific_domains():
    """Test specific domain checks."""
    print("\n" + "=" * 70)
    print("Disposable Domain Detection Test")
    print("=" * 70)
    
    disposable_emails = [
        "test@10minutemail.com",
        "user@guerrillamail.com",
        "temp@mailinator.com",
        "fake@tempmail.com",
    ]
    
    for email in disposable_emails:
        is_disposable = EmailValidator.is_disposable_email(email)
        status = "✅" if is_disposable else "❌"
        print(f"{status} {email} - Disposable: {is_disposable}")
    
    print("\n" + "=" * 70)
    print("Typo Suggestion Test")
    print("=" * 70)
    
    typo_emails = [
        "user@gmai.com",
        "user@gmial.com",
        "user@yahooo.com",
        "user@hotmial.com",
        "user@gmail.com",  # No typo
    ]
    
    for email in typo_emails:
        suggestion = EmailValidator.suggest_correction(email)
        if suggestion:
            print(f"💡 {email} → {suggestion}")
        else:
            print(f"✅ {email} - No correction needed")


if __name__ == '__main__':
    print("\n")
    success = test_email_validation()
    test_specific_domains()
    
    print("\n")
    if success:
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("⚠️  Some tests failed!")
        sys.exit(1)
