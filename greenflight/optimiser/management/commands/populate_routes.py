from django.core.management.base import BaseCommand
from optimiser.models import FlightRoute
import csv
import os
from django.conf import settings

class Command(BaseCommand):
    help = 'Populate database with flight routes from CSV file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-file',
            type=str,
            default='sample_routes.csv',
            help='Path to CSV file (default: sample_routes.csv in project root)'
        )

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        
        # If relative path, look in project root
        if not os.path.isabs(csv_file):
            csv_file = os.path.join(settings.BASE_DIR, csv_file)
        
        if not os.path.exists(csv_file):
            self.stdout.write(
                self.style.ERROR(f'CSV file not found: {csv_file}')
            )
            return

        created_count = 0
        updated_count = 0
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for row in reader:
                    route, created = FlightRoute.objects.get_or_create(
                        origin=row['origin'].strip(),
                        destination=row['destination'].strip(),
                        aircraft_type=row['aircraft_type'].strip(),
                        defaults={
                            'distance_km': float(row['distance_km']),
                            'fuel_burn_per_km': float(row['fuel_burn_per_km'])
                        }
                    )
                    
                    if created:
                        created_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'Created route: {route}')
                        )
                    else:
                        # Update existing route if data is different
                        updated = False
                        if route.distance_km != float(row['distance_km']):
                            route.distance_km = float(row['distance_km'])
                            updated = True
                        if route.fuel_burn_per_km != float(row['fuel_burn_per_km']):
                            route.fuel_burn_per_km = float(row['fuel_burn_per_km'])
                            updated = True
                        
                        if updated:
                            route.save()
                            updated_count += 1
                            self.stdout.write(
                                self.style.WARNING(f'Updated route: {route}')
                            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error reading CSV file: {str(e)}')
            )
            return

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully processed CSV file: {created_count} created, {updated_count} updated'
            )
        )
