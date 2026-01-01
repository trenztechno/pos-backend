from django.contrib import admin
from .models import SalesBackup

@admin.register(SalesBackup)
class SalesBackupAdmin(admin.ModelAdmin):
    list_display = ['id', 'vendor', 'device_id', 'synced_at', 'created_at']
    list_filter = ['vendor', 'synced_at', 'created_at']
    search_fields = ['device_id', 'id', 'vendor__business_name', 'vendor__user__username']
    readonly_fields = ['id', 'synced_at', 'created_at']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('vendor', 'vendor__user')
