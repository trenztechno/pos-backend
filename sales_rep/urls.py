from django.urls import path
from . import views

app_name = 'sales_rep'

urlpatterns = [
    path('', views.login_view, name='login'),
    path('vendors/', views.vendor_list, name='vendor_list'),
    path('vendors/<uuid:vendor_id>/', views.vendor_detail, name='vendor_detail'),
    path('vendors/<uuid:vendor_id>/approve/', views.approve_vendor, name='approve_vendor'),
    path('vendors/<uuid:vendor_id>/reject/', views.reject_vendor, name='reject_vendor'),
    path('vendors/<uuid:vendor_id>/activate/', views.activate_vendor, name='activate_vendor'),
    path('vendors/<uuid:vendor_id>/deactivate/', views.deactivate_vendor, name='deactivate_vendor'),
    path('vendors/bulk-approve/', views.bulk_approve, name='bulk_approve'),
]

