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

# Static files never change after the image is built, so collect them once here
# instead of on every container start. SECRET_KEY is only needed to import the
# settings module; the real one is supplied by the environment at runtime.
RUN SECRET_KEY=build-time-only python manage.py collectstatic --noinput

# Drop root. /app/media holds user uploads and must be a mounted volume to
# survive a redeploy; /app/logs is written at runtime. Both need to be writable
# by the unprivileged user.
RUN useradd --create-home --uid 10001 appuser && \
    mkdir -p /app/logs /app/media && \
    chmod 750 /app/logs && \
    chown -R appuser:appuser /app/logs /app/media

USER appuser

# Expose the port that the application will run on
EXPOSE 8000

# Command to run the application
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "1", "--timeout", "300"]
