"""
Django settings for DDHelper project.

Generated by 'django-admin startproject' using Django 3.2.7.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""
import os
import sys
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

TESTING = len(sys.argv) > 1 and sys.argv[1] == 'test'

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/


# Celery settings

CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'amqp://guest:guest@localhost')

#: Only add pickle to this list if your broker is secured
#: from unwanted access (see userguide/security.html)
CELERY_ACCEPT_CONTENT = ['json']
CELERY_RESULT_BACKEND = 'django-db'
CELERY_TASK_SERIALIZER = 'json'

CELERY_BEAT_SCHEDULE = {

}

CELERY_TASK_ROUTES = ([
    ('dynamic.tasks.*', {'queue': 'dynamic'}),
    ('biliapi.tasks.*', {'queue': 'biliapi'}),
],)

PROXY_POOL = os.environ.get('PROXY_POOL', 'http://edrows.top:5555/random')

if TESTING:
    PROXY_POOL = None
    CELERY_TASK_ALWAYS_EAGER = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-ftlcjkddikq@s5k*7+i4h-b(r%g6po%1cd2h40$uvz7cafhatc')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DJANGO_DEBUG', 'DEBUG') == 'DEBUG'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(';')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_celery_results',
    'django_celery_beat',
    'account',
    'dynamic',
    'subscribe'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'DDHelper.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'DDHelper.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('MYSQL_NAME', 'ddhelper'),
        'USER': os.environ.get('MYSQL_USER', 'root'),
        'PASSWORD': os.environ.get('MYSQL_PASSWORD', ''),
        'HOST': os.environ.get('MYSQL_HOST', '127.0.0.1'),
        'PORT': os.environ.get('MYSQL_PORT', 3306),
    }
}

# Email
EMAIL_HOST = os.environ.get('EMAIL_HOST', None)
EMAIL_PORT = os.environ.get('EMAIL_PORT', None)
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', None)
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', None)
EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', None)
PIN_EMAIL = os.environ.get('PIN_EMAIL', None)

AUTH_USER_MODEL = 'account.Userinfo'

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = '/static/'

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
