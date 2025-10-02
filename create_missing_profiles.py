import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flightcode.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import UserProfile

def create_missing_profiles():
    """Create UserProfile for any User that doesn't have one"""
    users_without_profiles = []
    
    for user in User.objects.all():
        try:
            # Check if profile exists
            profile = user.profile
        except:
            # Create profile if it doesn't exist
            users_without_profiles.append(user.username)
            UserProfile.objects.create(user=user)
            
    if users_without_profiles:
        print(f"Created profiles for users: {', '.join(users_without_profiles)}")
    else:
        print("No missing profiles found.")

if __name__ == "__main__":
    create_missing_profiles()
