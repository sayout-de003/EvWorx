from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import OnSiteRepairBooking, Order

User = get_user_model()

class AdminManagementTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser(username='admin', password='password', email='admin@test.com')
        self.regular_user = User.objects.create_user(username='user', password='password', email='user@test.com')
        self.repair_booking = OnSiteRepairBooking.objects.create(
            full_name='Test User', mobile_no='1234567890', vehicle_type='Bike',
            brand='Ola', model_no='S1', problem_details='Brakes', address='Road 1'
        )

    def test_admin_hub_access(self):
        # Regular user should be redirected
        self.client.login(username='user', password='password')
        response = self.client.get(reverse('admin_management_hub'))
        self.assertEqual(response.status_code, 302)
        
        # Admin user should have access
        self.client.login(username='admin', password='password')
        response = self.client.get(reverse('admin_management_hub'))
        self.assertEqual(response.status_code, 200)

    def test_repair_accept_reject(self):
        self.client.login(username='admin', password='password')
        # Accept
        self.client.post(reverse('admin_repair_list'), {'booking_id': self.repair_booking.id, 'action': 'accept'})
        self.repair_booking.refresh_from_db()
        self.assertEqual(self.repair_booking.status, 'Accepted')
        
        # Reject
        self.client.post(reverse('admin_repair_list'), {'booking_id': self.repair_booking.id, 'action': 'reject'})
        self.repair_booking.refresh_from_db()
        self.assertEqual(self.repair_booking.status, 'Rejected')

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
        booking = OnSiteRepairBooking.objects.filter(full_name='John Doe').first()
        self.assertEqual(booking.full_name, 'John Doe')
        self.assertEqual(booking.brand, 'Tesla')

    def test_onsite_repair_booking_post_invalid(self):
        data = {
            'full_name': '',
            'mobile_no': '9876543210',
            'vehicle_type': 'Car',
            'brand': 'Tesla',
            'model_no': 'Model S',
            'problem_details': 'Brakes are squeaking',
            'address': '123 Test St, Test City'
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
