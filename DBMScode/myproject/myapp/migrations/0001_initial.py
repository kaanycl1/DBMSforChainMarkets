# Generated by Django 5.1.4 on 2025-01-04 00:35

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('customer_id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50)),
                ('monthly_spending', models.DecimalField(decimal_places=2, max_digits=10)),
            ],
        ),
    ]
