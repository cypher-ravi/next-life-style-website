# Generated by Django 3.2 on 2021-05-06 13:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_item_additional_info'),
    ]

    operations = [
        migrations.CreateModel(
            name='Banner',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('b_image', models.ImageField(upload_to='banner')),
                ('b_title', models.CharField(max_length=30)),
                ('b_description1', models.TextField(max_length=30)),
                ('b_description2', models.TextField(max_length=30)),
            ],
        ),
    ]
