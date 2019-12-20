import os
from raven.contrib.django.client import DjangoClient


class OCDClient(DjangoClient):

    def send(self, **kwargs):

        # Warnings do not have exceptions
        if 'exception' not in kwargs:
            return super().send(**kwargs)

        # Ignore ScrapeError from empty hourly scrapes
        for value in kwargs['exception'].get('values', []):

            if value.get('type') == 'ScrapeError':

                extra = kwargs.get('extra', {})
                arg_v = extra.get('sys.argv')

                if arg_v:
                    for arg in arg_v:
                        if 'window' in arg:
                            return None

        return super().send(**kwargs)

CACHE_DIR = '/tmp/cache/_cache'
SCRAPED_DATA_DIR = '/tmp/cache/_data'
STATIC_ROOT = '/tmp'

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgis://opencivicdata:@localhost/opencivicdata')

SHARED_DB = os.environ.get('SHARED_DB') == 'True'
if SHARED_DB:
    # Heroku's DATABASE_URL will always indicate a Postgres engine, even if
    # PostGIS is installed. If we're scraping into a Councilmatic database,
    # then it must be corrected.
    if DATABASE_URL.startswith('postgres:'):
        engine, *parts = DATABASE_URL.split(':')
        parts = ['postgis'] + parts
        DATABASE_URL = ':'.join(parts)

    INSTALLED_APPS = (
        'django.contrib.contenttypes',
        'opencivicdata.core.apps.BaseConfig',
        'opencivicdata.legislative.apps.BaseConfig',
        'pupa',
        'councilmatic_core'
    )
    OCD_CITY_COUNCIL_NAME = None


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': "%(asctime)s %(levelname)s %(name)s: %(message)s",
            'datefmt': '%m/%d/%Y %H:%M:%S'
        }
    },
    'handlers': {
        'default': {'level': 'INFO',
                    'class': 'pupa.ext.ansistrm.ColorizingStreamHandler',
                    'formatter': 'standard'
                   },
        'sentry': {
            'level': 'CRITICAL',
            'class': 'raven.handlers.logging.SentryHandler',
            'client_cls': OCDClient,
            'dsn': '',
            },
    },
    'loggers': {
        '': {
            'handlers': ['default', 'sentry'], 'level': 'DEBUG', 'propagate': True
        },
        'scrapelib': {
            'handlers': ['default'], 'level': 'INFO', 'propagate': False
        },
        'requests': {
            'handlers': ['default'], 'level': 'WARN', 'propagate': False
        },
        'boto': {
            'handlers': ['default', 'sentry'], 'level': 'WARN', 'propagate': False
        },
        'django': {
            'handlers': ['default'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
    },
}