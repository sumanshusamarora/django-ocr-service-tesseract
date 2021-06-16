# Generated by Django 3.2.4 on 2021-06-16 04:44

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='OCRInput',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('guid', models.CharField(editable=False, max_length=100)),
                ('file', models.FileField(blank=True, help_text='File or Cloud storage URL/URI required', null=True, upload_to='input_pdfs')),
                ('cloud_storage_url_or_uri', models.CharField(blank=True, help_text='File or Cloud storage URL/URI required', max_length=1000, null=True)),
                ('bucket_name', models.CharField(blank=True, max_length=255, null=True)),
                ('filename', models.CharField(blank=True, max_length=255, null=True)),
                ('ocr_config', models.CharField(blank=True, max_length=255, null=True)),
                ('ocr_language', models.CharField(blank=True, max_length=50, null=True)),
                ('ocr_text', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
