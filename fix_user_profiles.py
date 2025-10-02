import os
import django
import subprocess
import sys

def fix_user_profiles():
    """Fix the missing UserProfile table by creating and applying migrations"""
    print("Starting UserProfile table fix...")
    
    # Set up Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flightcode.settings')
    django.setup()
    
    # Create initial migration if it doesn't exist
    migration_dir = os.path.join('accounts', 'migrations')
    if not os.path.exists(migration_dir):
        os.makedirs(migration_dir)
        print(f"Created migrations directory: {migration_dir}")
    
    init_file = os.path.join(migration_dir, '__init__.py')
    if not os.path.exists(init_file):
        with open(init_file, 'w') as f:
            pass
        print(f"Created {init_file}")
    
    # Run Django commands
    try:
        print("\nGenerating migrations for accounts app...")
        subprocess.run([sys.executable, 'manage.py', 'makemigrations', 'accounts'], check=True)
        
        print("\nApplying migrations...")
        subprocess.run([sys.executable, 'manage.py', 'migrate'], check=True)
        
        # Create profiles for existing users
        from django.contrib.auth.models import User
        from accounts.models import UserProfile
        
        print("\nCreating profiles for existing users...")
        users_without_profiles = []
        
        for user in User.objects.all():
            try:
                # Try accessing profile to check if it exists
                profile = user.profile
            except UserProfile.DoesNotExist:
                # Create profile if it doesn't exist
                users_without_profiles.append(user.username)
                UserProfile.objects.create(user=user)
                
        if users_without_profiles:
            print(f"Created profiles for users: {', '.join(users_without_profiles)}")
        else:
            print("No missing profiles found.")
            
        print("\nFix completed successfully!")
        print("You should now be able to log in without errors.")
        
    except subprocess.CalledProcessError as e:
        print(f"Error running Django command: {e}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False
        
    return True

if __name__ == "__main__":
    fix_user_profiles()
