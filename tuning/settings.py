"""
Django settings for tuning project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '$5n73rcxx(nk#4ix92rbia%zd-x^^4g&gwnx=9!1o_j%9_aue@'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []

SITE_ID = 1



MEDIA_ROOT = os.path.join(BASE_DIR, 'site_media')
MEDIA_URL = '/site_media/'

STATIC_ROOT = os.path.join(BASE_DIR, 'shared_static')
STATIC_URL = '/shared_static/'




## Additional locations of static files
# STATICFILES_DIRS = (
#    os.path.join(PROJECT_ROOT, 'pricing_data'),
# )

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',

)


TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.media",
    'django.core.context_processors.request',
    'django.core.context_processors.static',
    'django.contrib.messages.context_processors.messages',
    'web.context_processors.add_stuff',

)



MIDDLEWARE_CLASSES = (

    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
    )


LOGIN_REDIRECT_URL = '/'

DEFAULT_FROM_EMAIL = 'info@tunings.com'

#SESSION_EXPIRE_AT_BROWSER_CLOSE = True
#SESSION_COOKIE_AGE = 1800   # 30 mins

APPEND_SLASH = True
FILE_UPLOAD_PERMISSIONS = 0644



TEMPLATE_DIRS = (
    BASE_DIR+ "/templates",

    )




# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django_google_maps',
    'django_cron',
    'fluent_comments',
    'crispy_forms',
    'django.contrib.comments',
    'bootstrap3',
    'theme',  # holds themeforest template
    'web',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'privateviews.middleware.LoginRequiredMiddleware',
)

ROOT_URLCONF = 'tuning.urls'

WSGI_APPLICATION = 'tuning.wsgi.application'


INTERNAL_IPS = ('217.115.117.19',)
ALLOWED_HOSTS = [
    '.tunemypiano.co.uk',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'tuning',                      # Or path to database file if using sqlite3.
        'USER': 'tuning',                      # Not used with sqlite3.
        'PASSWORD': 'thornhill',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
        'OPTIONS': { 'init_command': 'SET storage_engine=MyISAM;' }
    }
}


# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-uk'

TIME_ZONE = 'Europe/London'

USE_I18N = False

USE_L10N = True

USE_TZ = True

SITE_ID = 1

FLUENT_COMMENTS_EXCLUDE_FIELDS = ('name', 'email', 'url')
COMMENTS_APP = 'fluent_comments'


AUTH_USER_MODEL = "web.CustomUser"

FAKEDATE_FILE = "fakedate.txt"
USE_FAKEDATES = False

# time in minutes to make each appointment unless specified
DEFAULT_SLOT_TIME = 60
MAX_BOOK_DAYS_IN_ADVANCE = 380
SLA_ASSIGN_TUNER = 60   # minutes to assign tuner

API_URL = "http://tunemypiano.co.uk/api/v1/"


CRON_CLASSES = [
    "web.cron.CheckBookingStatus",

]

#TODO: more sophisticated privacy - https://github.com/dabapps/django-private-views

DATETIME_FORMAT = "D N j, P"
try:
    from tuning.settings_local import *
except ImportError:
    pass

