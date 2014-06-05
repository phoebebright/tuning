"""
Development decisions:
1. Put as much logic as possible in the model.  Views should just serve data.
2. As far as possible use the api rather than views/django template tags so that it is more
portable, however, in the interests of getting it done, some template tags are used.
3. Timezones - all database dates are utc.  On the django side dates are are utc EXCEPT,
where a new deadline is being created and the default time is local.
Javascript handles the conversion from utc for display and passed back utc to the api
Tried every possible combination of where the conversion could be done and all other options
seemed to end up in a mess with stray conversions.  This approach means django only has to
know about the clients timezone when creating a default date, and this could be easily changed
in future so that the default is created at the javascript end.


"""
from __future__ import absolute_import

#TODO: Assess data models for speed - need to remove null=true I think

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
#TODO: https://github.com/frankwiles/django-app-metrics
#http://iambusychangingtheworld.blogspot.ie/2013/04/asynchronously-sending-email-using.html
''' starting instructions
rabbitmq-server
rabbitmqctl status

monitor: http://127.0.0.1:15672/#/connections

start:
    celery -A tuning worker -B -l info

http://micewww.pp.rl.ac.uk/projects/maus/wiki/MAUSCelery

monitor:
    pip install flower  - install
    celery flower -- run
    http://localhost:5555  --view

to setup as daemons
http://docs.celeryproject.org/en/latest/tutorials/daemonizing.html#daemonizing

'''
# settings up celery periodic tasks http://stackoverflow.com/questions/20116573/in-celery-3-1-making-django-periodic-task


from celery.schedules import crontab



CELERYBEAT_SCHEDULE = {
    # crontab(hour=0, minute=0, day_of_week='saturday')
    'check-bookings-to-complete': {
        'task': 'web.tasks.check_bookings',
        'schedule': crontab(),    # every n minutes crontab(minute='*/15')
    },
    'email-monitor-send': {
        'task': 'email_monitor.tasks.send',
        'schedule': crontab(),
        },
    'email-monitor-check': {
        'task': 'email_monitor.tasks.check',
        'schedule': crontab(1),
        },
    }

# didn't think this was required
CELERY_IMPORTS = ('web.tasks', 'email_monitor.tasks')

CELERY_MONITOR_URL = "http://217.115.117.19:5555"
RABBITMQ_MONITOR_URL = "http://217.115.117.19:55672"

# import djcelery
# djcelery.setup_loader()
BROKER_URL = "amqp://guest:guest@localhost:5672/"

# usernames to cc on all notifications
NOTIFICATIONS_CC = ['pbright', 'system']

NOTIFICATION_BACKENDS = [
    ("email", "notification.backends.email_logged.EmailLoggedBackend"),
    ]

DEFAULT_FROM_EMAIL = "system@tunemypiano.co.uk"
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
'''
EMAIL_HOST = "mail.beautifuldata.ie"
EMAIL_PORT = "25"
EMAIL_HOST_USER = "test@beautifuldata.ie"
EMAIL_HOST_PASSWORD = "cabbage123"
'''

MONITOR_IMAP_SERVER = "mail.tunemypiano.co.uk"
MONITOR_IMAP_PASSWORD = "Hg76bbqq"

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '$5n73rcxx(nk#4ix92rbia%zd-x^^4g&gwnx=9!1o_j%9_aue@'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []

SITE_ID = 1

ADMINS = (
    ('Phoebe', 'phoebebright310+tune@gmail.com'),
)
NOTIFY_BOOKINGS = ['phoebebright310+notifybook@gmail.com',]

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
    'django.contrib.admindocs',
    'django_google_maps',
    'django_cron',
    'theme',  # holds themeforest template static files
    'django_gravatar',
    'notification',
    # 'djcelery',
    #'djcelery_email',
    #'django_twilio',
    'django_logtail',
    'email_monitor',
    'web',
    'django_statsd',
)

MIDDLEWARE_CLASSES = (
    'django_statsd.middleware.StatsdMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'privateviews.middleware.LoginRequiredMiddleware',
    'django_statsd.middleware.StatsdMiddlewareTimer',
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

TIME_ZONE = 'UTC'  # for django and database
USER_TIME_ZONE = "Europe/London"  # for converting data to/from javascript


USE_I18N = False

USE_L10N = False

USE_TZ = True

SITE_ID = 1



AUTHENTICATION_BACKENDS = (
    'web.models.CustomAuth',
    'django.contrib.auth.backends.ModelBackend',)


AUTH_USER_MODEL = "web.CustomUser"


FAKEDATE_FILE = "fakedate.txt"
USE_FAKEDATES = False

# time in minutes to make each appointment unless specified
DEFAULT_DEADLINE_TIME = "09:00"
DEFAULT_SLOT_TIME = 60
MAX_BOOK_DAYS_IN_ADVANCE = 380
SLA_ASSIGN_TUNER = 60   # minutes to assign tuner


# calendar settings

CALENDAR_MIN_TIME = "05:00:00"
CALENDAR_MAX_TIME = "22:00:00"

API_URL = "http://tunemypiano.co.uk/api/v1/"


CRON_CLASSES = [
    "web.cron.CheckBookingStatus",

    ]

#TODO: more sophisticated privacy - https://github.com/dabapps/django-private-views

TWILIO_ACCOUNT_SID = 'PN78be7b924df23239bd6d439537561152'
TWILIO_AUTH_TOKEN = '6ba9663e89e284de2e7a11c08e79fac4'

DATETIME_FORMAT = "D j N P"
SHORT_DATE_FORMAT = "D j N"
TIME_FORMAT = "P"
TASTYPIE_DATETIME_FORMATTING = 'iso-8601-strict'  # eg.  2010-12-16T03:02:00



LOGTAIL_FILES = {
    'apache': '/var/log/apache2/error.log',
    'celery': os.path.join(BASE_DIR, 'logs/celery.log'),
    'logfile': os.path.join(BASE_DIR, 'logs/logfile.log'),
    }

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'simple': {
            'format': '%(levelname)s %(message)s',
            'datefmt': '%y %b %d, %H:%M:%S',
            },

        'standard': {
            'format' : "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt' : "%d/%b/%Y %H:%M:%S"
        },
        },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'logfile': {
            'level':'DEBUG',
            'class':'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/logfile.log'),
            'maxBytes': 50000,
            'backupCount': 2,
            'formatter': 'standard',
            },
        'celery': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/celery.log'),
            'formatter': 'simple',
            'maxBytes': 1024 * 1024 * 100,  # 100 mb

        },
        },
    'loggers': {
        'django': {
            'handlers':['console'],
            'propagate': True,
            'level':'WARN',
            },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
            },
        'web': {
            'handlers': ['console', 'logfile'],
            'level': 'DEBUG',
            },
        'celery': {
            'handlers': ['celery', 'console'],
            'level': 'DEBUG',
            },
        }
}

from logging.config import dictConfig
dictConfig(LOGGING)


try:
    from tuning.settings_local import *
except ImportError:
    pass

