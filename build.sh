#!/usr/bin/env bash
# Exit on error
set -o errexit

# Note: Chrome installation removed due to Render.com limitations
# Crawling will be handled by GitHub Actions instead

# Install Python dependencies
uv sync

# Collect static files
uv run python manage.py collectstatic --no-input

# Run migrations
uv run python manage.py migrate

# Setup initial data
uv run python manage.py shell -c "
from notices.tasks import setup_initial_data
try:
    setup_initial_data()
    print('Initial data setup completed')
except Exception as e:
    print(f'Initial data setup failed: {e}')
"

# Setup periodic tasks for Celery Beat
uv run python manage.py setup_periodic_tasks

# Create superuser for admin access
uv run python manage.py shell -c "
from django.contrib.auth import get_user_model
import os
User = get_user_model()
username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@knu-notice.com')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'knu-admin-2025!')

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f'Superuser {username} created successfully')
else:
    print(f'Superuser {username} already exists')
"
