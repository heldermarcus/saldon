# Generated manually - Remove account_type from Account model

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_alter_user_plan'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='account',
            name='account_type',
        ),
    ]
