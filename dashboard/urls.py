from django.urls import path
from .views import (
    dashboard_stats,
    dashboard_sales,
    dashboard_items,
    dashboard_payments,
    dashboard_tax,
    dashboard_profit,
    dashboard_dues
)

urlpatterns = [
    path('stats', dashboard_stats, name='dashboard-stats'),
    path('sales', dashboard_sales, name='dashboard-sales'),
    path('items', dashboard_items, name='dashboard-items'),
    path('payments', dashboard_payments, name='dashboard-payments'),
    path('tax', dashboard_tax, name='dashboard-tax'),
    path('profit', dashboard_profit, name='dashboard-profit'),
    path('dues', dashboard_dues, name='dashboard-dues'),
]

