#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

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

# Create a superuser if not already created
echo "Creating superuser..."
echo "from django.contrib.auth import get_user_model; \
      User = get_user_model(); \
      User.objects.filter(username='admin').exists() or \
      User.objects.create_superuser('admin', 'admin@example.com', 'password')" | python manage.py shell

# Start the Django server
echo "Starting server..."
exec "$@"
