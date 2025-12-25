# Generated migration to add year and rate fields to Stock model

from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_initial'),
    ]

    operations = [
        # Add year field with default value
        migrations.AddField(
            model_name='stock',
            name='year',
            field=models.IntegerField(default=2079, help_text='Fiscal year (e.g., 2078, 2079)'),
            preserve_default=False,
        ),
        # Add rate fields
        migrations.AddField(
            model_name='stock',
            name='diamond_rate',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), help_text='Diamond rate per gram', max_digits=12),
        ),
        migrations.AddField(
            model_name='stock',
            name='gold_rate',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), help_text='Gold rate per gram', max_digits=12),
        ),
        migrations.AddField(
            model_name='stock',
            name='silver_rate',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), help_text='Silver rate per gram', max_digits=12),
        ),
        # Update jardi field to be DecimalField with 2 decimal places
        migrations.AlterField(
            model_name='stock',
            name='jardi',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), help_text='Jardi amount in currency', max_digits=10),
        ),
        # Add unique constraint to year
        migrations.AlterField(
            model_name='stock',
            name='year',
            field=models.IntegerField(help_text='Fiscal year (e.g., 2078, 2079)', unique=True),
        ),
        # Update model ordering and verbose names
        migrations.AlterModelOptions(
            name='stock',
            options={'ordering': ['-year'], 'verbose_name': 'Stock', 'verbose_name_plural': 'Stock'},
        ),
    ]
