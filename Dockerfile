# Use the official Python image as the base image
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# core/wsgi.py falls back to settings.local-development (DEBUG=True) when this
# is unset, so pin the deployed default here. Override at runtime for stage.
ENV DJANGO_SETTINGS_MODULE=settings.prod

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /app/

# Drop root. STATIC_ROOT (/app/assets) is a named volume shared with the Caddy
# container, /app/media holds user uploads, and /app/logs is written at runtime,
# so all three must be writable by the unprivileged user.
#
# collectstatic also runs here, not just at startup: Docker seeds an *empty*
# named volume from the image, copying both the contents and this ownership. So
# a freshly created volume comes out appuser-owned and needs no host setup. A
# volume that already has content keeps whatever ownership it already had, and
# must be handed over once on the host:
#   docker run --rm -v household_static:/v alpine chown -R 10001:10001 /v
RUN useradd --create-home --uid 10001 appuser && \
    SECRET_KEY=build-time-only python manage.py collectstatic --noinput && \
    mkdir -p /app/logs /app/media && \
    chmod 750 /app/logs && \
    chown -R appuser:appuser /app/assets /app/logs /app/media

USER appuser

# Expose the port that the application will run on
EXPOSE 8000

# collectstatic has to run on every start, not only at build: /app/assets is a
# named volume mounted over the image's copy, so the build-time output is
# invisible unless that volume happened to be empty. Caddy serves the volume,
# so this is what makes a static change actually reach the browser.
# `exec` hands PID 1 to gunicorn so it receives SIGTERM on shutdown.
CMD ["sh", "-c", "python manage.py collectstatic --noinput && exec gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 1 --timeout 300"]
