#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Run migrations
python manage.py migrate

# Setup initial data
python manage.py shell -c "
from notices.tasks import setup_initial_data
try:
    setup_initial_data()
    print('Initial data setup completed')
except Exception as e:
    print(f'Initial data setup failed: {e}')
"

# Add dummy data for testing
python manage.py add_dummy_data
