from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'y)0a&-2=1v#dsed_=^wa!$+wvn#&++0jr8koc1owp*^uqa9lqt'

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = ['*'] 

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


INSTALLED_APPS = INSTALLED_APPS + [
    'django_extensions',
    'wagtail.contrib.styleguide',
]

# MIDDLEWARE = MIDDLEWARE + [
#     'debug_toolbar.middleware.DebugToolbarMiddleware',
# ]

# INTERNAL_IPS = ('127.0.0.1', '172.17.0.1')

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': 'C:\wamp64\www\demos\wagtail_course\mysite\cache'
    }
}

try:
    from .local import *
except ImportError:
    pass
