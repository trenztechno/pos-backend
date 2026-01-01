from django.db import models
import uuid

class SalesBackup(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.ForeignKey('auth_app.Vendor', on_delete=models.CASCADE, related_name='sales_backups', null=True, blank=True)
    bill_data = models.JSONField()  # Store the entire bill blob from mobile
    device_id = models.CharField(max_length=255, blank=True, null=True)
    synced_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-synced_at']
        indexes = [
            models.Index(fields=['id']),
            models.Index(fields=['vendor', 'synced_at']),
            models.Index(fields=['device_id']),
        ]
    
    def __str__(self):
        return f"Bill {self.id} from {self.vendor.business_name or self.vendor.user.username} ({self.device_id or 'Unknown'})"
