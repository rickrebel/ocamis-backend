# Generated by Django 4.1.6 on 2023-04-23 05:43

import ckeditor.fields
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SendGridProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, unique=True)),
                ('sendgrid_api_key', models.CharField(max_length=255)),
                ('webhook_slug', models.CharField(blank=True, max_length=255, null=True)),
                ('from_email', models.CharField(max_length=100)),
                ('default', models.BooleanField(default=False)),
                ('test_mode', models.BooleanField(default=False)),
                ('test_emails', models.CharField(blank=True, max_length=255, null=True)),
            ],
            options={
                'verbose_name': 'Perfil de correo por SendGrid',
                'verbose_name_plural': 'Perfiles de correo por SendGrid',
            },
        ),
        migrations.CreateModel(
            name='TemplateBase',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(max_length=200)),
                ('from_name', models.CharField(max_length=200)),
                ('name', models.CharField(max_length=200, null=True)),
                ('body', ckeditor.fields.RichTextField()),
                ('description', models.TextField(blank=True, null=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('sendgrid_profile', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='email_sendgrid.sendgridprofile')),
            ],
            options={
                'verbose_name': 'Plantilla Base',
                'verbose_name_plural': 'Plantillas Base',
                'db_table': 'perfil_templatebase',
            },
        ),
        migrations.CreateModel(
            name='MassMailing',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('filter_kwargs', models.TextField(blank=True, null=True)),
                ('exclude_kwargs', models.TextField(blank=True, null=True)),
                ('order_by_args', models.TextField(blank=True, null=True)),
                ('template_base', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='email_sendgrid.templatebase')),
            ],
            options={
                'db_table': 'perfil_massmailing',
            },
        ),
        migrations.CreateModel(
            name='EmailRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('send_email', models.BooleanField(default=False)),
                ('email', models.CharField(blank=True, max_length=120, null=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('x_message_id', models.CharField(blank=True, max_length=120, null=True)),
                ('sg_message_id', models.CharField(blank=True, max_length=120, null=True)),
                ('status', models.CharField(default='unknown', max_length=20)),
                ('status_date', models.DateTimeField(blank=True, null=True)),
                ('type_message', models.CharField(blank=True, max_length=100, null=True)),
                ('sendgrid_profile', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='email_sendgrid.sendgridprofile')),
                ('template_base', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='email_sendgrid.templatebase')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Envio de Email',
                'verbose_name_plural': 'Envios de Emails',
                'db_table': 'perfil_emailrecord',
            },
        ),
        migrations.CreateModel(
            name='EmailEventHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event', models.CharField(max_length=20)),
                ('response_date', models.DateTimeField(auto_now_add=True)),
                ('event_data', models.TextField()),
                ('email_record', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='email_sendgrid.emailrecord')),
            ],
            options={
                'db_table': 'perfil_emaileventhistory',
            },
        ),
    ]
