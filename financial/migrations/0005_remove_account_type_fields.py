# Generated manually - Remove account_type fields from financial models

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('financial', '0004_transactionhistory'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='category',
            name='account_type',
        ),
        migrations.RemoveField(
            model_name='customer',
            name='account_type',
        ),
        migrations.RemoveField(
            model_name='sale',
            name='account_type',
        ),
        migrations.RemoveField(
            model_name='transactionhistory',
            name='account_type',
        ),
    ]
