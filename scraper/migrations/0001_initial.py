# Generated by Django 5.1.5 on 2025-02-27 23:19

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ScrapedData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_identifier', models.CharField(help_text='Unique identifier for the user', max_length=255)),
                ('url', models.URLField()),
                ('product_name', models.CharField(max_length=255)),
                ('current_price', models.CharField(max_length=50)),
                ('previous_price', models.CharField(blank=True, max_length=50, null=True)),
                ('discount', models.CharField(blank=True, max_length=20, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
