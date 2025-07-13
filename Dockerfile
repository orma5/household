# Use the official Python image as the base image
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt /app/

# Install dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Create the logs directory
RUN mkdir -p /app/logs && chmod 750 /app/logs

# Copy the current directory contents into the container at /app
COPY . /app/

# Expose the port that the application will run on
EXPOSE 8000

# Command to run the application
CMD ["sh", "-c", "python manage.py collectstatic --noinput && gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 1 --timeout 300"]