# Generated by Django 2.1.11 on 2020-05-18 08:43

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('applications', '0005_lmtwallet'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lmtwallet',
            name='create_time',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='充值时间'),
        ),
    ]
