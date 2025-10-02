#!/usr/bin/env python
import os
import sys
import subprocess
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flightcode.settings')
django.setup()

def create_migration_dirs():
    """Ensure migration directories exist for all apps"""
    apps = ['accounts', 'optimiser']
    
    for app in apps:
        migration_dir = os.path.join(app, 'migrations')
        if not os.path.exists(migration_dir):
            os.makedirs(migration_dir)
            print(f"Created missing migrations directory: {migration_dir}")
        
        init_file = os.path.join(migration_dir, '__init__.py')
        if not os.path.exists(init_file):
            with open(init_file, 'w') as f:
                pass
            print(f"Created {init_file}")

def reset_migrations():
    """Recreate migrations from scratch"""
    try:
        # First make sure migration directories exist
        create_migration_dirs()
        
        # Create fresh migrations
        print("\n=== Creating fresh migrations ===")
        subprocess.run([sys.executable, 'manage.py', 'makemigrations'], check=True)
        
        # Apply migrations
        print("\n=== Applying migrations ===")
        subprocess.run([sys.executable, 'manage.py', 'migrate'], check=True)
        
        # Create user profiles if needed
        from django.contrib.auth.models import User
        from accounts.models import UserProfile
        
        print("\n=== Creating missing user profiles ===")
        users_without_profiles = []
        
        for user in User.objects.all():
            profile, created = UserProfile.objects.get_or_create(user=user)
            if created:
                users_without_profiles.append(user.username)
        
        if users_without_profiles:
            print(f"Created profiles for users: {', '.join(users_without_profiles)}")
        else:
            print("All users already have profiles.")
        
        print("\n✅ DATABASE FIX COMPLETE!")
        print("You should now be able to log in without errors.")
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ ERROR running Django command: {e}")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    print("Starting database fix...\n")
    success = reset_migrations()
    if not success:
        print("\nFix did not complete successfully. Please check the errors above.")
        sys.exit(1)
    else:
        print("\nFix completed successfully! You can now restart your server.")
