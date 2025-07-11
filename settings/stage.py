from .common import *  # noqa

DEBUG = False

ALLOWED_HOSTS = ["*"]

CSRF_TRUSTED_ORIGINS = ["https://*.dkms.se"]


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