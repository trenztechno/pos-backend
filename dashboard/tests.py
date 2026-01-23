from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from datetime import date, timedelta
from decimal import Decimal

from auth_app.models import Vendor
from sales.models import Bill, BillItem
from items.models import Item, Category


class DashboardStatsTestCase(TestCase):
    """Test dashboard stats endpoint"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create vendor
        self.user = User.objects.create_user(username='testvendor', password='test123')
        self.vendor = Vendor.objects.create(
            user=self.user,
            business_name='Test Restaurant',
            gst_no='29TEST1234F1Z5',
            is_approved=True
        )
        self.user.is_active = True
        self.user.save()
        
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        # Create test bills
        today = date.today()
        self.bill1 = Bill.objects.create(
            vendor=self.vendor,
            invoice_number='INV-001',
            bill_date=today,
            billing_mode='gst',
            subtotal=Decimal('100.00'),
            total_amount=Decimal('118.00'),
            total_tax=Decimal('18.00'),
            cgst_amount=Decimal('9.00'),
            sgst_amount=Decimal('9.00'),
            payment_mode='cash'
        )
        
        self.bill2 = Bill.objects.create(
            vendor=self.vendor,
            invoice_number='INV-002',
            bill_date=today,
            billing_mode='non_gst',
            subtotal=Decimal('200.00'),
            total_amount=Decimal('200.00'),
            total_tax=Decimal('0.00'),
            payment_mode='upi'
        )
    
    def test_dashboard_stats_success(self):
        """Test successful dashboard stats retrieval"""
        response = self.client.get('/dashboard/stats/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('statistics', response.data)
        self.assertEqual(response.data['statistics']['total_bills'], 2)
        self.assertEqual(response.data['statistics']['gst_bills'], 1)
        self.assertEqual(response.data['statistics']['non_gst_bills'], 1)
    
    def test_dashboard_stats_with_date_range(self):
        """Test dashboard stats with date range"""
        yesterday = date.today() - timedelta(days=1)
        response = self.client.get(f'/dashboard/stats/?start_date={yesterday}&end_date={date.today()}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_dashboard_stats_unauthorized(self):
        """Test dashboard stats without authentication"""
        self.client.credentials()
        response = self.client.get('/dashboard/stats/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class DashboardSalesTestCase(TestCase):
    """Test dashboard sales endpoint"""
    
    def setUp(self):
        self.client = APIClient()
        
        self.user = User.objects.create_user(username='testvendor', password='test123')
        self.vendor = Vendor.objects.create(
            user=self.user,
            business_name='Test Restaurant',
            gst_no='29TEST1234F1Z5',
            is_approved=True
        )
        self.user.is_active = True
        self.user.save()
        
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
    
    def test_dashboard_sales_success(self):
        """Test successful dashboard sales retrieval"""
        response = self.client.get('/dashboard/sales/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('summary', response.data)
    
    def test_dashboard_sales_with_billing_mode_filter(self):
        """Test dashboard sales with billing mode filter"""
        response = self.client.get('/dashboard/sales/?billing_mode=gst')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['filters']['billing_mode'], 'gst')


class DashboardItemsTestCase(TestCase):
    """Test dashboard items endpoint"""
    
    def setUp(self):
        self.client = APIClient()
        
        self.user = User.objects.create_user(username='testvendor', password='test123')
        self.vendor = Vendor.objects.create(
            user=self.user,
            business_name='Test Restaurant',
            gst_no='29TEST1234F1Z5',
            is_approved=True
        )
        self.user.is_active = True
        self.user.save()
        
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        # Create category and item
        self.category = Category.objects.create(name='Beverages', vendor=self.vendor)
        self.item = Item.objects.create(
            vendor=self.vendor,
            name='Coca Cola',
            price=Decimal('25.00'),
            mrp_price=Decimal('25.00'),
            gst_percentage=Decimal('18.00')
        )
        self.item.categories.add(self.category)
        
        # Create bill with item
        self.bill = Bill.objects.create(
            vendor=self.vendor,
            invoice_number='INV-001',
            bill_date=date.today(),
            billing_mode='gst',
            subtotal=Decimal('25.00'),
            total_amount=Decimal('29.50'),
            total_tax=Decimal('4.50')
        )
        
        BillItem.objects.create(
            bill=self.bill,
            item=self.item,
            item_name='Coca Cola',
            price=Decimal('25.00'),
            mrp_price=Decimal('25.00'),
            quantity=Decimal('1.00'),
            subtotal=Decimal('25.00'),
            gst_percentage=Decimal('18.00'),
            item_gst_amount=Decimal('4.50')
        )
    
    def test_dashboard_items_most_sold(self):
        """Test dashboard items with most_sold sort"""
        response = self.client.get('/dashboard/items/?sort=most_sold')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('items', response.data)
    
    def test_dashboard_items_least_sold(self):
        """Test dashboard items with least_sold sort"""
        response = self.client.get('/dashboard/items/?sort=least_sold')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class DashboardPaymentsTestCase(TestCase):
    """Test dashboard payments endpoint"""
    
    def setUp(self):
        self.client = APIClient()
        
        self.user = User.objects.create_user(username='testvendor', password='test123')
        self.vendor = Vendor.objects.create(
            user=self.user,
            business_name='Test Restaurant',
            gst_no='29TEST1234F1Z5',
            is_approved=True
        )
        self.user.is_active = True
        self.user.save()
        
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
    
    def test_dashboard_payments_success(self):
        """Test successful dashboard payments retrieval"""
        response = self.client.get('/dashboard/payments/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('payment_split', response.data)


class DashboardTaxTestCase(TestCase):
    """Test dashboard tax endpoint"""
    
    def setUp(self):
        self.client = APIClient()
        
        self.user = User.objects.create_user(username='testvendor', password='test123')
        self.vendor = Vendor.objects.create(
            user=self.user,
            business_name='Test Restaurant',
            gst_no='29TEST1234F1Z5',
            is_approved=True
        )
        self.user.is_active = True
        self.user.save()
        
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
    
    def test_dashboard_tax_success(self):
        """Test successful dashboard tax retrieval"""
        response = self.client.get('/dashboard/tax/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('summary', response.data)


class DashboardProfitTestCase(TestCase):
    """Test dashboard profit endpoint"""
    
    def setUp(self):
        self.client = APIClient()
        
        self.user = User.objects.create_user(username='testvendor', password='test123')
        self.vendor = Vendor.objects.create(
            user=self.user,
            business_name='Test Restaurant',
            gst_no='29TEST1234F1Z5',
            is_approved=True
        )
        self.user.is_active = True
        self.user.save()
        
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
    
    def test_dashboard_profit_success(self):
        """Test successful dashboard profit retrieval"""
        response = self.client.get('/dashboard/profit/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('profit_calculation', response.data)

