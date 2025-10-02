from django.core.management.base import BaseCommand
from optimiser.models import FlightRoute

class Command(BaseCommand):
    help = 'Check flight routes data in the database'

    def add_arguments(self, parser):
        parser.add_argument('--origin', type=str, help='Filter by origin')
        parser.add_argument('--destination', type=str, help='Filter by destination')
        parser.add_argument('--aircraft', type=str, help='Filter by aircraft type')

    def handle(self, *args, **options):
        queryset = FlightRoute.objects.all()
        
        if options['origin']:
            queryset = queryset.filter(origin=options['origin'])
        
        if options['destination']:
            queryset = queryset.filter(destination=options['destination'])
            
        if options['aircraft']:
            queryset = queryset.filter(aircraft_type=options['aircraft'])
        
        count = queryset.count()
        self.stdout.write(self.style.SUCCESS(f'Found {count} routes matching criteria'))
        
        for route in queryset:
            self.stdout.write(
                f'Route {route.id}: {route.origin} → {route.destination} ({route.aircraft_type}), '
                f'Distance: {route.distance_km}km, Fuel: {route.fuel_consumption_kg}kg'
            )
            
        if count == 0:
            self.stdout.write(self.style.WARNING('No matching routes found. Make sure you have loaded sample data.'))
            self.stdout.write('Try running: python manage.py load_sample_routes --csv-file=optimiser/sample_routes.csv')
