# Generated migration to convert discount system to percentage-based

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0003_create_bill_models'),
    ]

    operations = [
        # Remove item-level discount fields from BillItem
        migrations.RemoveField(
            model_name='billitem',
            name='additional_discount',
        ),
        migrations.RemoveField(
            model_name='billitem',
            name='discount_amount',
        ),
        # Remove discount_amount field from Bill (now calculated as property from discount_percentage)
        migrations.RemoveField(
            model_name='bill',
            name='discount_amount',
        ),
        # Update Bill model help text to clarify discount_percentage is primary
        migrations.AlterField(
            model_name='bill',
            name='discount_percentage',
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text='Discount percentage applied to subtotal (before tax)',
                max_digits=5,
                validators=[django.core.validators.MinValueValidator(0)]
            ),
        ),
    ]

