# Generated manually for bill numbering configuration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth_app', '0008_vendor_security_pin'),
    ]

    operations = [
        migrations.AddField(
            model_name='vendor',
            name='bill_prefix',
            field=models.CharField(blank=True, help_text="Prefix for bill numbers (e.g., 'INV', 'BILL', 'REST'). Format: {prefix}-{date}-{number}", max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='vendor',
            name='bill_starting_number',
            field=models.IntegerField(default=1, help_text='Starting bill number (to account for existing bills before system migration)'),
        ),
        migrations.AddField(
            model_name='vendor',
            name='last_bill_number',
            field=models.IntegerField(default=0, help_text='Last generated bill number (for sequential generation, auto-incremented)'),
        ),
    ]

