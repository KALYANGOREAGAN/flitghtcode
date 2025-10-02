import csv
import os
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from optimiser.models import FlightRoute


class Command(BaseCommand):
    help = 'Load sample flight routes from CSV file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='/home/robat/Desktop/flightcode/data/sample_routes.csv',
            help='Path to CSV file (default: /home/robat/Desktop/flightcode/data/sample_routes.csv)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing routes before loading new ones'
        )

    def handle(self, *args, **options):
        csv_file_path = options['file']
        
        # Check if file exists
        if not os.path.exists(csv_file_path):
            raise CommandError(f'CSV file not found: {csv_file_path}')

        # Clear existing routes if requested
        if options['clear']:
            deleted_count = FlightRoute.objects.count()
            FlightRoute.objects.all().delete()
            self.stdout.write(
                self.style.WARNING(f'Deleted {deleted_count} existing routes')
            )

        # Load routes from CSV
        created_count = 0
        updated_count = 0
        error_count = 0

        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                
                for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 to account for header
                    try:
                        # Clean and validate data
                        origin = row['origin'].strip()
                        destination = row['destination'].strip()
                        distance_km = float(row['distance_km'])
                        aircraft_type = row['aircraft_type'].strip()
                        fuel_burn_per_km = float(row['fuel_burn_per_km'])
                        
                        # Validate required fields
                        if not all([origin, destination, aircraft_type]):
                            self.stdout.write(
                                self.style.ERROR(f'Row {row_num}: Missing required fields')
                            )
                            error_count += 1
                            continue
                        
                        if distance_km <= 0 or fuel_burn_per_km <= 0:
                            self.stdout.write(
                                self.style.ERROR(f'Row {row_num}: Invalid numeric values')
                            )
                            error_count += 1
                            continue
                        
                        # Create or update route
                        route, created = FlightRoute.objects.get_or_create(
                            origin=origin,
                            destination=destination,
                            aircraft_type=aircraft_type,
                            defaults={
                                'distance_km': distance_km,
                                'fuel_burn_per_km': fuel_burn_per_km
                            }
                        )
                        
                        if created:
                            created_count += 1
                            self.stdout.write(f'Created: {route}')
                        else:
                            # Update existing route if data has changed
                            if (route.distance_km != distance_km or 
                                route.fuel_burn_per_km != fuel_burn_per_km):
                                route.distance_km = distance_km
                                route.fuel_burn_per_km = fuel_burn_per_km
                                route.save()
                                updated_count += 1
                                self.stdout.write(f'Updated: {route}')
                    
                    except (ValueError, KeyError) as e:
                        self.stdout.write(
                            self.style.ERROR(f'Row {row_num}: Error processing data - {str(e)}')
                        )
                        error_count += 1
                        continue
                    
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'Row {row_num}: Unexpected error - {str(e)}')
                        )
                        error_count += 1
                        continue

        except Exception as e:
            raise CommandError(f'Error reading CSV file: {str(e)}')

        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS(f'✓ Routes created: {created_count}'))
        self.stdout.write(self.style.SUCCESS(f'✓ Routes updated: {updated_count}'))
        
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'✗ Errors encountered: {error_count}'))
        
        total_routes = FlightRoute.objects.count()
        self.stdout.write(self.style.SUCCESS(f'✓ Total routes in database: {total_routes}'))
        self.stdout.write('='*50)
        
        if created_count > 0 or updated_count > 0:
            self.stdout.write(
                self.style.SUCCESS('Sample routes loaded successfully!')
            )
        else:
            self.stdout.write(
                self.style.WARNING('No new routes were loaded.')
            )
