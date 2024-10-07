import os
from dotenv import load_dotenv
from core.settings.get_env import getenv_bool, getenv_int, getenv_list, getenv_db

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'
WSGI_APPLICATION = 'core.wsgi.application'
ASGI_APPLICATION = 'core.asgi.application'
ROOT_URLCONF = 'core.urls'
DATA_UPLOAD_MAX_MEMORY_SIZE = getenv_int(
    "DATA_UPLOAD_MAX_MEMORY_SIZE", 2000242880)

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
    "geo.apps.GeoConfig",
    "medicine.apps.MedicineConfig",
    "intl_medicine.apps.IntlMedicineConfig",
    "email_sendgrid.apps.EmailSendgridConfig",
    "formula.apps.FormulaConfig",
    "mat.apps.MatConfig",
    "data_param.apps.DataParamConfig",
    "med_cat.apps.MedCatConfig",
    "inai.apps.InaiConfig",
    "respond.apps.RespondConfig",
    "transparency.apps.TransparencyConfig",
    "category.apps.CategoryConfig",
    "classify_task.apps.ClassifyTaskConfig",
    "task.apps.TaskConfig",
    "rds.apps.RdsConfig",
    'ckeditor',
    'rest_framework.authtoken',
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

# ---------------------------------DATABASE----------------------------------
DATABASES = {
    'default': getenv_db(
        engine=os.getenv("DB_MAIN_ENGINE", "postgres"), base_dir=BASE_DIR)
}

IS_BIG_ACTIVE = getenv_bool("IS_BIG_ACTIVE", False)
USE_BIG_DB_DATABASE = getenv_bool("USE_BIG_DB_DATABASE", False)

if USE_BIG_DB_DATABASE:
    DATABASES['big_db'] = getenv_db(
        env_pref="BIG_DB",
        engine=os.getenv("BIG_DB_ENGINE", "postgres"),
        base_dir=BASE_DIR
    )
    DATABASE_ROUTERS = ['core.routers.OcamisRouter']

SITE_ID = getenv_int("SITE_ID", 1)
# -------------------------------END DATABASE--------------------------------

# ---------------------------------SECURITY-----------------------------------

SECRET_KEY = os.getenv("DESABASTO_SECRET_KEY", "secret_key_value")
# SECRET_KEY = os.getenv("DESABASTO_SECRET_KEY", "SECRET_KEY_value")
ALLOWED_HOSTS = getenv_list("ALLOWED_HOSTS", ["*"])

DEBUG = getenv_bool("DESABASTO_DEBUG", True)
DEBUG_FRONT = getenv_bool("DEBUG_FRONT", True)
IS_PRODUCTION = getenv_bool("DESABASTO_PROD", False)
IS_LOCAL = getenv_bool("DESABASTO_LOCAL", True)

CAN_DELETE_AWS_STORAGE_FILES = getenv_bool(
    "CAN_DELETE_AWS_STORAGE_FILES", False)

CORS_ORIGIN_ALLOW_ALL = getenv_bool("CORS_ORIGIN_ALLOW_ALL", True)
_CSRF_TRUSTED_ORIGINS = getenv_list("CSRF_TRUSTED_ORIGINS")
if _CSRF_TRUSTED_ORIGINS:
    CSRF_TRUSTED_ORIGINS = _CSRF_TRUSTED_ORIGINS
USE_X_FORWARDED_HOST = getenv_bool("USE_X_FORWARDED_HOST", True)
HTTP_X_FORWARDED_HOST = os.getenv("HTTP_X_FORWARDED_HOST")

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

# -------------------------------END SECURITY---------------------------------

# ----------------------------INTERNATIONALIZATION----------------------------

LANGUAGE_CODE = os.getenv("LANGUAGE_CODE", 'es-mx')

TIME_ZONE = os.getenv("TIME_ZONE", 'America/Mexico_City')

USE_I18N = getenv_bool("USE_I18N", True)

USE_L10N = getenv_bool("USE_L10N", True)

USE_TZ = getenv_bool("USE_TZ", True)
# --------------------------END INTERNATIONALIZATION--------------------------

# -----------------------------API REST FRAMEWORK-----------------------------
SITE_URL = os.getenv("DESABASTO_SITE_URL")
API_URL = os.getenv("DESABASTO_API_URL")

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
# ---------------------------END API REST FRAMEWORK---------------------------

# -----------------------------------EMAIL-----------------------------------
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
EMAIL_PORT = getenv_int("EMAIL_PORT", 587)
EMAIL_USE_TLS = getenv_bool("EMAIL_USE_TLS", True)
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL")
SERVER_EMAIL = DEFAULT_FROM_EMAIL
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
# ---------------------------------END EMAIL---------------------------------

# ----------------------------------CELERY-----------------------------------
DESPACHADOR_CELERY = getenv_bool("DESPACHADOR_CELERY", False)
USE_LOCAL_LAMBDA = getenv_bool("USE_LOCAL_LAMBDA", True)

BROKER_URL = os.getenv("BROKER_URL")
CELERY_TASK_SERIALIZER = os.getenv("CELERY_TASK_SERIALIZER", 'json')
CELERY_RESULT_SERIALIZER = os.getenv("CELERY_RESULT_SERIALIZER", 'json')
CELERY_ENABLE_UTC = getenv_bool("CELERY_ENABLE_UTC", True)
CELERY_ACCEPT_CONTENT = getenv_list("CELERY_ACCEPT_CONTENT", ['json'])

# --------------------------------END CELERY---------------------------------

# ----------------------------------CHANELS----------------------------------
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            'hosts': getenv_list(
                "CHANNEL_LAYERS_DEFAULT_HOSTS", ['redis://localhost:6379']
            ),
        },
    },
}
DEFAULT_CHANNEL_LAYER = os.getenv("DEFAULT_CHANNEL_LAYER", "default")
# --------------------------------END CHANELS--------------------------------

# ---------------------------------STORAGE-----------------------------------
COMPRESS_ENABLED = getenv_bool("COMPRESS_ENABLED", True)
COMPRESS_OFFLINE = getenv_bool("COMPRESS_OFFLINE", True)


AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME')
AWS_PRELOAD_METADATA = getenv_bool('AWS_PRELOAD_METADATA', True)

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')

AWS_LOCATION = os.getenv('AWS_LOCATION')
AWS_DEFAULT_ACL = os.getenv('AWS_DEFAULT_ACL', 'public-read')
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com'

AWS_STATIC_LOCATION = os.getenv('AWS_STATIC_LOCATION', 'static_compressed')
STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

AWS_S3_FILE_OVERWRITE = getenv_bool('AWS_S3_FILE_OVERWRITE', False)

URL_AMAZON_S3_FILES_UPLOADED = os.getenv('URL_AMAZON_S3_FILES_UPLOADED')

AWS_IS_GZIPPED = getenv_bool('AWS_IS_GZIPPED', False)

GZIP_CONTENT_TYPES = set(getenv_list('GZIP_CONTENT_TYPES', []))

if AWS_STORAGE_BUCKET_NAME:
    INSTALLED_APPS += ("storages", )
# -------------------------------END STORAGE---------------------------------

# ----------------------------------MEDIA------------------------------------
STATIC_PATH = os.path.join(BASE_DIR, os.getenv("STATIC_PATH", 'static'))
MEDIA_PATH = os.path.join(BASE_DIR, os.getenv("MEDIA_PATH", 'media'))

LOCALE_PATHS = (
    os.path.join(BASE_DIR, os.getenv("LOCALE_PATH", '../locale')),
)


UPLOAD_FOLDER_IMG = os.path.join(MEDIA_PATH, 'image', '')
UPLOAD_FOLDER_IMG_PROFILE = os.path.join(MEDIA_PATH, 'profile', '')
UPLOAD_FOLDER_TMP = os.path.join(BASE_DIR, "media/temp/")

MEDIA_URL = os.getenv("MEDIA_URL", "/media/")
AWS_MEDIA_URL = f'https://{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com'

COMPRESS_URL = os.getenv("COMPRESS_URL", "/static/")
STATIC_URL = os.getenv("STATIC_URL", "/static/")
STATIC_ROOT = os.path.join(
    BASE_DIR, os.getenv("STATIC_ROOT", 'static_compressed'))

COMPRESS_ROOT = STATIC_ROOT

MEDIA_ROOT = MEDIA_PATH

# ------------------------------END MEDIA------------------------------------

# ---------------------------------TEMPLATES---------------------------------
TEMPLATE_PATH = os.path.join(BASE_DIR, os.getenv("TEMPLATE_PATH", 'templates'))
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
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
# -------------------------------END TEMPLATES-------------------------------
