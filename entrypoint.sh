#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Set DJANGO_ENV for Docker environment
export DJANGO_ENV=${DJANGO_ENV:-docker}

# Function to wait for the PostgreSQL database to be ready
function wait_for_db() {
  until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER"; do
    echo "Waiting for database to be ready..."
    sleep 2
  done
}

# Wait for the database to be ready
wait_for_db

# Run migrations
echo "Running migrations..."
python manage.py migrate

# Start the Django server
echo "Starting server..."
exec "$@"
echo "Server running on 127.0.0.1:8000 and localhost:8000"
