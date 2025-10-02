#!/bin/bash

echo "Fixing accounts app database issues..."

# Activate virtual environment
source venv/bin/activate

# Generate migrations for the accounts app
echo "Generating migrations for accounts app..."
python manage.py makemigrations accounts

# Apply all migrations
echo "Applying migrations..."
python manage.py migrate

# Run script to create profiles for existing users
echo "Creating missing user profiles..."
python create_missing_profiles.py

echo "Done! The accounts app should now work correctly."
