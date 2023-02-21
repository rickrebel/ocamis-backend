"""
Django settings for core project.

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import os
import json

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_PATH = os.path.join(BASE_DIR, 'templates')
STATIC_PATH = os.path.join(BASE_DIR, 'static')
MEDIA_PATH = os.path.join(BASE_DIR, 'media')
#FILES_PATH = os.path.join(BASE_DIR, 'data_files')

LOCALE_PATHS = (
    os.path.join(BASE_DIR, '../locale'),
)


"""desabasto_allowed_hosts = os.getenv("DESABASTO_ALLOWED_HOSTS")
if desabasto_allowed_hosts:
    try:
        hosts = json.loads(os.getenv("DESABASTO_ALLOWED_HOSTS"))
    except Exception:
        hosts = [host.strip() for host in desabasto_allowed_hosts.split(",")]
else:
    if DEBUG:
        hosts = ["*"]
    else:
        hosts = []
ALLOWED_HOSTS = hosts"""
ALLOWED_HOSTS = ["*"]

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    #     'django.template.loaders.eggs.Loader',
)


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            TEMPLATE_PATH,
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                # Insert your TEMPLATE_CONTEXT_PROCESSORS here or use this
                # list if you haven't customized them:
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.request',
            ],
        },
    },
]


INSTALLED_APPS = [
    "daphne",
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    "channels",
    "rest_framework",
    "channels_redis",
    "corsheaders",
    # "desabasto.apps.DesabastoConfig",
    "catalog.apps.CatalogConfig",
    "medicine.apps.MedicineConfig",
    "report.apps.ReportConfig",
    "intl_medicine.apps.IntlMedicineConfig",
    "email_sendgrid.apps.EmailSendgridConfig",
    'ckeditor',
    'rest_framework.authtoken',
    "formula.apps.FormulaConfig",
    "data_param.apps.DataParamConfig",
    "inai.apps.InaiConfig",
    "category.apps.CategoryConfig",
    "task.apps.TaskConfig",
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


WSGI_APPLICATION = 'core.wsgi.application'
ASGI_APPLICATION = 'core.asgi.application'
ROOT_URLCONF = 'core.urls'

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            # 'hosts': [('localhost', 6379)],
            'hosts': ['redis://localhost:6379'],
        },
    },
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.'
        'UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.'
        'MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.'
        'CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.'
        'NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'es-mx'

TIME_ZONE = 'America/Mexico_City'


USE_I18N = True

USE_L10N = True

USE_TZ = True


REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
        'core.authentication.BearerAuthentication',
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    )
}

DEFAULT_CHANNEL_LAYER = "default"
