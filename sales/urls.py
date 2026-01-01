from django.urls import path
from .views import SalesSyncView

urlpatterns = [
    path('sync', SalesSyncView.as_view(), name='sales-sync'),
]

