#!/usr/bin/env python
import os
import sys
import django

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flightcode.settings')
django.setup()

def main():
    """Fix the missing UserProfile table in the database"""
    from django.core.management import call_command
    from django.contrib.auth.models import User
    
    print("=== Creating UserProfile Table Fix ===")
    
    # Make sure migrations directory exists
    migrations_dir = os.path.join('accounts', 'migrations')
    if not os.path.exists(migrations_dir):
        os.makedirs(migrations_dir)
        open(os.path.join(migrations_dir, '__init__.py'), 'a').close()
        print(f"Created migrations directory: {migrations_dir}")
    
    try:
        # Generate migrations for accounts app
        print("\n[1/3] Generating migrations for accounts app...")
        call_command('makemigrations', 'accounts')
        
        # Apply migrations
        print("\n[2/3] Applying migrations...")
        call_command('migrate')
        
        # Create profiles for users
        print("\n[3/3] Creating profiles for existing users...")
        from accounts.models import UserProfile
        
        created_count = 0
        for user in User.objects.all():
            # Check if profile exists
            try:
                user.profile
            except UserProfile.DoesNotExist:
                # Create profile
                UserProfile.objects.create(user=user, bio="")
                created_count += 1
        
        print(f"Created {created_count} missing user profiles")
        print("\n✅ Database fix completed successfully!")
        print("You can now log in without errors.")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    main()
