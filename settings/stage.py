from .common import *  # noqa

DEBUG = False

ALLOWED_HOSTS = ["*"]

CSRF_TRUSTED_ORIGINS = ["https://*.dkms.se"]

# TLS terminates at a reverse proxy in front of this app.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
# Kept short since *.dkms.se is a wildcard shared with other homelab services;
# raise once HTTPS is confirmed reliable for this app specifically.
SECURE_HSTS_SECONDS = 3600


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "format": (
                '{{"level": "{levelname}", "time": "{asctime}", '
                '"module": "{module}", "message": "{message}"}}'
            ),
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
        "common": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "inventory": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "product": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "purchase": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "shopify": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}