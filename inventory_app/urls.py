from django.urls import path
from .views import (
    InventoryListView,
    InventoryDetailView,
    InventoryStockUpdateView,
    InventoryUnitTypesView,
)

app_name = 'inventory'

urlpatterns = [
    path('', InventoryListView.as_view(), name='inventory-list'),
    path('unit-types/', InventoryUnitTypesView.as_view(), name='inventory-unit-types'),
    path('<uuid:id>/', InventoryDetailView.as_view(), name='inventory-detail'),
    path('<uuid:id>/stock/', InventoryStockUpdateView.as_view(), name='inventory-stock-update'),
]

