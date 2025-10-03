from django.core.management.base import BaseCommand
from django.db import connection, ProgrammingError
from django.core.management import call_command
import time

class Command(BaseCommand):
    help = 'Initialize the database with required tables and sample data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting database initialization...'))

        # Wait for database to be fully available (useful in containerized environments)
        self.ensure_database_connection()
        
        # Apply migrations first
        self.stdout.write('Applying migrations...')
        call_command('migrate', '--noinput')
        
        # Verify essential tables exist
        self.verify_and_create_tables()
        
        # Create sample data if needed
        self.create_sample_data()
        
        self.stdout.write(self.style.SUCCESS('Database initialization completed successfully'))
    
    def ensure_database_connection(self):
        """Ensure database is available before proceeding"""
        max_attempts = 5
        attempt = 0
        
        while attempt < max_attempts:
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    return
            except Exception as e:
                attempt += 1
                self.stdout.write(self.style.WARNING(
                    f"Database connection attempt {attempt}/{max_attempts} failed: {str(e)}"
                ))
                if attempt < max_attempts:
                    time.sleep(2)  # Wait before retrying
        
        self.stdout.write(self.style.ERROR("Could not connect to the database after multiple attempts"))
    
    def verify_and_create_tables(self):
        """Verify all required tables exist"""
        essential_tables = [
            'optimiser_flightroute',
            'optimiser_emissionrecord',
            'optimiser_passengerecoscore'
        ]
        
        for table in essential_tables:
            self.verify_table_exists(table)
    
    def verify_table_exists(self, table_name):
        """Verify a specific table exists and recreate if needed"""
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                self.stdout.write(self.style.SUCCESS(f"Table '{table_name}' exists with {count} records"))
        except ProgrammingError:
            self.stdout.write(self.style.WARNING(f"Table '{table_name}' does not exist, creating..."))
            
            # Determine app name from table name
            app_name = table_name.split('_')[0]
            
            # Create the table by applying specific migrations
            call_command('migrate', app_name, '--noinput')
            
            # Verify again
            try:
                with connection.cursor() as cursor:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    self.stdout.write(self.style.SUCCESS(f"Table '{table_name}' created with {count} records"))
            except ProgrammingError:
                self.stdout.write(self.style.ERROR(f"Failed to create table '{table_name}'"))
    
    def create_sample_data(self):
        """Create sample flight routes if the table is empty"""
        try:
            from optimiser.models import FlightRoute
            
            # Check if we have routes
            if FlightRoute.objects.exists():
                self.stdout.write(self.style.SUCCESS(f"Found {FlightRoute.objects.count()} existing flight routes"))
                return
                
            # Create sample routes
            sample_routes = [
                {"origin": "ENTEBBE", "destination": "NAIROBI", "aircraft_type": "Boeing 737-800", "distance_km": 500, "fuel_consumption_kg": 1800},
                {"origin": "ENTEBBE", "destination": "NAIROBI", "aircraft_type": "Airbus A320", "distance_km": 500, "fuel_consumption_kg": 1750},
                {"origin": "LONDON", "destination": "PARIS", "aircraft_type": "Airbus A220-300", "distance_km": 340, "fuel_consumption_kg": 1200},
                {"origin": "LONDON", "destination": "PARIS", "aircraft_type": "Boeing 737-800", "distance_km": 340, "fuel_consumption_kg": 1350},
                {"origin": "NAIROBI", "destination": "DAR ES SALAAM", "aircraft_type": "Embraer E190", "distance_km": 430, "fuel_consumption_kg": 1400},
                {"origin": "NEW YORK", "destination": "WASHINGTON", "aircraft_type": "Airbus A320", "distance_km": 330, "fuel_consumption_kg": 1250},
            ]
            
            created_count = 0
            for route_data in sample_routes:
                FlightRoute.objects.create(**route_data)
                created_count += 1
            
            self.stdout.write(self.style.SUCCESS(f"Created {created_count} sample flight routes"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error creating sample data: {str(e)}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error creating sample data: {str(e)}"))
