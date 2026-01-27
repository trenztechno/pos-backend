from django.urls import path
from .views import SalesSyncView, BillListView, BillDetailView

# Sync URLs (for /backup/ path)
sync_urlpatterns = [
    path('sync', SalesSyncView.as_view(), name='sales-sync'),
]

# Bill CRUD URLs (for /bills/ path)
bill_urlpatterns = [
    path('', BillListView.as_view(), name='bill-list'),
    path('<uuid:bill_id>/', BillDetailView.as_view(), name='bill-detail'),
]

# Default export (for backward compatibility - sync endpoints)
urlpatterns = sync_urlpatterns

