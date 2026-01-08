from django.urls import path
from .views import (
    InventoryListView,
    InventoryDetailView,
    StockUpdateView,
    UnitTypesView,
)

app_name = 'inventory'

urlpatterns = [
    path('', InventoryListView.as_view(), name='inventory-list'),
    path('unit-types/', UnitTypesView.as_view(), name='unit-types'),
    path('<uuid:id>/', InventoryDetailView.as_view(), name='inventory-detail'),
    path('<uuid:id>/stock/', StockUpdateView.as_view(), name='stock-update'),
]

