# Generated by Django 3.2.7 on 2021-11-14 08:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0004_auto_20210911_1657'),
    ]

    operations = [
        migrations.AddField(
            model_name='stock',
            name='logo',
            field=models.ImageField(blank=True, null=True, upload_to=''),
        ),
    ]
