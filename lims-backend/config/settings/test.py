from .development import *

DEBUG = False

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Use a faster password hasher for tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Disable any unnecessary middleware or features for tests
# For example, if you have a custom middleware that relies on external services
# MIDDLEWARE = [
#     m for m in MIDDLEWARE if m not in [
#         'apps.some_app.middleware.SomeCustomMiddleware',
#     ]
# ]
