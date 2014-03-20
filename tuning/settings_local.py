import settings
import os


INTERNAL_IPS = ('127.0.0.1', '217.115.117.19',)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(settings.BASE_DIR, 'db.sqlite3'),
    }
}

USE_FAKEDATES = True
DEBUG = True