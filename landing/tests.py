import pytest
from django.urls import reverse
from rest_framework import status


# ============================================
# LANDING PAGE TESTS (Public Pages)
# ============================================

@pytest.mark.django_db
class TestLandingPages:
    """Test all landing/public pages load correctly"""
    
    def test_home_page_loads(self, client):
        """Verify home page loads successfully"""
        response = client.get(reverse('landing:home'))
        
        assert response.status_code == 200
    
    def test_about_page_loads(self, client):
        """Verify about page loads successfully"""
        response = client.get(reverse('landing:about'))
        
        assert response.status_code == 200
    
    # def test_contact_page_loads(self, client):
        # """Verify contact page loads successfully"""
        # response = client.get(reverse('landing:contact'))
        
        # assert response.status_code == 200
    
    def test_services_page_loads(self, client):
        """Verify services page loads successfully"""
        response = client.get(reverse('landing:services'))
        
        assert response.status_code == 200
    
    def test_service_details_page_loads(self, client):
        """Verify service details page loads successfully"""
        response = client.get(reverse('landing:service_details'))
        
        assert response.status_code == 200
    
    def test_team_page_loads(self, client):
        """Verify team page loads successfully"""
        response = client.get(reverse('landing:team'))
        
        assert response.status_code == 200
    
    # def test_team_details_page_loads(self, client):
        # """Verify team details page loads successfully"""
        # response = client.get(reverse('landing:team_details'))
        
        # assert response.status_code == 200
    
    def test_appointment_page_loads(self, client):
        """Verify appointment page loads successfully"""
        response = client.get(reverse('landing:appointment'))
        
        assert response.status_code == 200
    
    # def test_faq_page_loads(self, client):
        # """Verify FAQ page loads successfully"""
        # response = client.get(reverse('landing:faq'))
        
        # assert response.status_code == 200


# @pytest.mark.django_db
# class TestContactForm:
#     """Test contact form functionality"""
    
#     def test_contact_form_post_redirects(self, client):
#         """Verify contact form submission redirects"""
#         response = client.post(reverse('landing:contact'), {
#             'name': 'Test User',
#             'email': 'test@example.com',
#             'message': 'This is a test message'
#         })
        
#         # Should redirect after successful submission
#         assert response.status_code == 302
#         assert '/contact/' in response.url


@pytest.mark.django_db
class TestAppointmentForm:
    """Test appointment form functionality"""
    
    def test_appointment_form_post_redirects(self, client):
        """Verify appointment form submission redirects"""
        response = client.post(reverse('landing:appointment'), {
            'name': 'Test User',
            'email': 'test@example.com',
            'number': '1234567890',
            'subject': 'General',
            'date': '2024-12-01',
            'time': '10:00'
        })
        
        # Should redirect after successful submission
        assert response.status_code == 302