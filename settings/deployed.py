"""Shared configuration for the deployed environments (stage and prod).

Both import from here so the hardening below cannot drift between them. Put
genuinely environment-specific overrides in stage.py / prod.py.
"""

from .common import *

DEBUG = False

# Anything addressing the app by raw container/pod IP (a k8s httpGet probe, for
# example) gets a 400 under this default and must either send a matching Host
# header or be added via the env var.
ALLOWED_HOSTS = env.list(
    "ALLOWED_HOSTS", default=[".dkms.se", "localhost", "127.0.0.1"]
)

CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=["https://*.dkms.se"])

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
        "upkeep": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
