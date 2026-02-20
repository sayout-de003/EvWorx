from django.test import TestCase, Client
from django.urls import reverse
from .models import OnSiteRepairBooking

class OnSiteRepairBookingTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('onsite_repair_booking')

    def test_onsite_repair_booking_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/onsite_repair_booking.html')

    def test_onsite_repair_booking_post_valid(self):
        data = {
            'full_name': 'John Doe',
            'mobile_no': '9876543210',
            'vehicle_type': 'Car',
            'brand': 'Tesla',
            'model_no': 'Model S',
            'problem_details': 'Brakes are squeaking',
            'address': '123 Test St, Test City'
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)  # Redirect to homepage
        self.assertEqual(OnSiteRepairBooking.objects.count(), 1)
        booking = OnSiteRepairBooking.objects.first()
        self.assertEqual(booking.full_name, 'John Doe')
        self.assertEqual(booking.brand, 'Tesla')

    def test_onsite_repair_booking_post_invalid(self):
        data = {
            'full_name': '',  # Required field missing
            'mobile_no': '9876543210',
            'vehicle_type': 'Car',
            'brand': 'Tesla',
            'model_no': 'Model S',
            'problem_details': 'Brakes are squeaking',
            'address': '123 Test St, Test City'
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)  # Re-renders form with errors
        self.assertEqual(OnSiteRepairBooking.objects.count(), 0)
