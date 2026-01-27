"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from backend.views import health_check
from sales.urls import sync_urlpatterns, bill_urlpatterns

urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('admin/', admin.site.urls),
    path('auth/', include('auth_app.urls')),
    path('items/', include('items.urls')),
    path('inventory/', include('inventory_app.urls')),
    path('backup/', include(sync_urlpatterns)),  # Sync endpoints: /backup/sync
    path('bills/', include(bill_urlpatterns)),  # Bill CRUD endpoints: /bills/ and /bills/<id>/
    path('settings/', include('settings.urls')),
    path('sales-rep/', include('sales_rep.urls')),
    path('dashboard/', include('dashboard.urls')),
]

# Serve media files in development (only for local storage)
if settings.DEBUG and not getattr(settings, 'USE_S3', False):
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
