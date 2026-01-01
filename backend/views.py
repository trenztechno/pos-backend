from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.db import connection
from django.core.cache import cache
from django.utils import timezone
import django
import sys
from django.conf import settings

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint - returns server status, database connectivity, and version info
    No authentication required - useful for monitoring and load balancers
    """
    health_status = {
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'version': '1.0.0',
        'services': {}
    }
    
    overall_healthy = True
    
    # Check database connectivity
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        health_status['services']['database'] = {
            'status': 'healthy',
            'message': 'Database connection successful'
        }
    except Exception as e:
        health_status['services']['database'] = {
            'status': 'unhealthy',
            'message': f'Database connection failed: {str(e)}'
        }
        overall_healthy = False
    
    # Check cache (if configured)
    try:
        cache.set('health_check_test', 'ok', 10)
        cache.get('health_check_test')
        health_status['services']['cache'] = {
            'status': 'healthy',
            'message': 'Cache is working'
        }
    except Exception as e:
        health_status['services']['cache'] = {
            'status': 'unhealthy',
            'message': f'Cache failed: {str(e)}'
        }
        # Cache failure is not critical, don't mark overall as unhealthy
    
    # Get basic system info
    health_status['system'] = {
        'django_version': django.get_version(),
        'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        'debug_mode': settings.DEBUG,
    }
    
    # Get database stats (if database is healthy)
    if health_status['services']['database']['status'] == 'healthy':
        try:
            from django.contrib.auth.models import User
            from auth_app.models import Vendor
            from items.models import Item, Category
            from sales.models import SalesBackup
            
            health_status['stats'] = {
                'users': User.objects.count(),
                'vendors': Vendor.objects.count(),
                'items': Item.objects.count(),
                'categories': Category.objects.count(),
                'sales_backups': SalesBackup.objects.count(),
            }
        except Exception as e:
            health_status['stats'] = {
                'error': f'Could not fetch stats: {str(e)}'
            }
    
    # Set overall status
    if not overall_healthy:
        health_status['status'] = 'unhealthy'
        return Response(health_status, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    return Response(health_status, status=status.HTTP_200_OK)

