# Generated by Django 2.0.7 on 2018-07-09 12:47

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('measurements', '0002_auto_20180626_1015'),
    ]

    operations = [
        migrations.RenameField(
            model_name='instancerunresult',
            old_name='pings',
            new_name='ping_response',
        ),
    ]