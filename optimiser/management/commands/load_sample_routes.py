import csv
import os
from django.core.management.base import BaseCommand
from optimiser.models import FlightRoute

class Command(BaseCommand):
    help = 'Loads sample flight routes data from CSV file'

    def add_arguments(self, parser):
        parser.add_argument('--csv-file', type=str, help='Path to the CSV file')

    def handle(self, *args, **kwargs):
        csv_file_path = kwargs['csv_file']
        
        if not os.path.exists(csv_file_path):
            self.stdout.write(self.style.ERROR(f'File {csv_file_path} does not exist'))
            return
        
        routes_created = 0
        routes_updated = 0
        
        with open(csv_file_path, 'r') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                route, created = FlightRoute.objects.update_or_create(
                    origin=row['origin'],
                    destination=row['destination'],
                    aircraft_type=row['aircraft_type'],
                    defaults={
                        'distance_km': float(row['distance_km']),
                        'fuel_consumption_kg': float(row['fuel_consumption_kg']),
                    }
                )
                
                if created:
                    routes_created += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'Created route: {route}')
                    )
                else:
                    routes_updated += 1
                    self.stdout.write(
                        self.style.WARNING(f'Updated route: {route}')
                    )
        
        self.stdout.write(self.style.SUCCESS(
            f'Successfully imported {routes_created} new routes and updated {routes_updated} routes'
        ))
