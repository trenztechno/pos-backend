from django.urls import path
from .views import (
    ItemListView, ItemDetailView, ItemStatusView, ItemSyncView,
    CategoryListView, CategoryDetailView, CategorySyncView
)

urlpatterns = [
    # Categories
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('categories/sync', CategorySyncView.as_view(), name='category-sync'),
    path('categories/<uuid:id>/', CategoryDetailView.as_view(), name='category-detail'),
    
    # Items
    path('', ItemListView.as_view(), name='item-list'),
    path('sync', ItemSyncView.as_view(), name='item-sync'),
    path('<uuid:id>/', ItemDetailView.as_view(), name='item-detail'),
    path('<uuid:id>/status/', ItemStatusView.as_view(), name='item-status'),
]
