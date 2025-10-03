from django.core.management.base import BaseCommand
from django.db import connection, ProgrammingError

class Command(BaseCommand):
    help = 'Ensures the database is properly set up with required tables'

    def handle(self, *args, **options):
        self.stdout.write('Checking database setup...')
        
        # Check if FlightRoute table exists
        with connection.cursor() as cursor:
            try:
                cursor.execute("SELECT COUNT(*) FROM optimiser_flightroute")
                count = cursor.fetchone()[0]
                self.stdout.write(self.style.SUCCESS(f'FlightRoute table exists with {count} records'))
            except ProgrammingError:
                self.stdout.write(self.style.WARNING('FlightRoute table does not exist, creating sample data...'))
                
                # Apply migrations again to be sure
                from django.core.management import call_command
                call_command('migrate', 'optimiser', '--noinput')
                
                # Create sample flight routes
                from optimiser.models import FlightRoute
                
                # Sample data
                routes_data = [
                    {"origin": "ENTEBBE", "destination": "NAIROBI", "aircraft_type": "Boeing 737-800", "distance_km": 500, "fuel_consumption_kg": 1800},
                    {"origin": "ENTEBBE", "destination": "NAIROBI", "aircraft_type": "Airbus A320", "distance_km": 500, "fuel_consumption_kg": 1750},
                    {"origin": "LONDON", "destination": "PARIS", "aircraft_type": "Airbus A220-300", "distance_km": 340, "fuel_consumption_kg": 1200},
                    {"origin": "LONDON", "destination": "PARIS", "aircraft_type": "Boeing 737-800", "distance_km": 340, "fuel_consumption_kg": 1350},
                    {"origin": "NAIROBI", "destination": "DAR ES SALAAM", "aircraft_type": "Embraer E190", "distance_km": 430, "fuel_consumption_kg": 1400},
                    {"origin": "NEW YORK", "destination": "WASHINGTON", "aircraft_type": "Airbus A320", "distance_km": 330, "fuel_consumption_kg": 1250},
                ]
                
                created_count = 0
                for data in routes_data:
                    FlightRoute.objects.create(**data)
                    created_count += 1
                
                self.stdout.write(self.style.SUCCESS(f'Created {created_count} sample flight routes'))
        
        # Verify other required tables
        required_tables = [
            'optimiser_emissionrecord',
            'optimiser_passengerecoscore',
            'accounts_userprofile',
        ]
        
        for table in required_tables:
            with connection.cursor() as cursor:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    self.stdout.write(self.style.SUCCESS(f'{table} exists with {count} records'))
                except ProgrammingError:
                    self.stdout.write(self.style.WARNING(f'{table} does not exist, applying migrations'))
                    # Apply specific app migrations
                    app_name = table.split('_')[0]
                    from django.core.management import call_command
                    call_command('migrate', app_name, '--noinput')

        self.stdout.write(self.style.SUCCESS('Database setup completed successfully'))
