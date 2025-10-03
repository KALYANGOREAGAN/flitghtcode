from django.core.management.base import BaseCommand
from optimiser.models import FlightRoute
import itertools

class Command(BaseCommand):
    help = 'Generate missing routes between all airports and aircraft combinations'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Force regeneration of all routes')

    def handle(self, *args, **options):
        # Get all distinct origins, destinations and aircraft types
        origins = set(FlightRoute.objects.values_list('origin', flat=True).distinct())
        destinations = set(FlightRoute.objects.values_list('destination', flat=True).distinct())
        aircraft_types = set(FlightRoute.objects.values_list('aircraft_type', flat=True).distinct())
        
        self.stdout.write(f'Found {len(origins)} origins, {len(destinations)} destinations, and {len(aircraft_types)} aircraft types')
        
        # Generate all possible combinations
        existing_routes = 0
        new_routes = 0
        skipped_routes = 0
        
        # Use airport distances if available, or estimate based on existing routes
        distance_map = {}
        
        # Build distance map from existing routes
        for route in FlightRoute.objects.all():
            key = (route.origin, route.destination)
            if key not in distance_map:
                distance_map[key] = route.distance_km
        
        # Create all combinations
        for origin, destination, aircraft in itertools.product(origins, destinations, aircraft_types):
            # Skip routes to self
            if origin == destination:
                continue
                
            # Check if route already exists
            if FlightRoute.objects.filter(
                origin=origin, destination=destination, aircraft_type=aircraft
            ).exists():
                existing_routes += 1
                continue
                
            # Use known distance if available or estimate
            key = (origin, destination)
            if key in distance_map:
                distance_km = distance_map[key]
            else:
                reverse_key = (destination, origin)
                if reverse_key in distance_map:
                    distance_km = distance_map[reverse_key]
                else:
                    # Skip if we can't determine distance
                    skipped_routes += 1
                    continue
            
            # Estimate fuel consumption based on aircraft type and distance
            # This is a simplistic model and could be improved
            base_consumption = {
                'Boeing 737-800': 3.5,
                'Boeing 737-700': 3.6,
                'Boeing 737-900ER': 3.4,
                'Boeing 787-8': 3.0,
                'Boeing 787-9': 2.9,
                'Boeing 777-300ER': 3.8,
                'Airbus A320': 3.4,
                'Airbus A320neo': 3.2,
                'Airbus A350-900': 2.9,
                'Airbus A330-300': 3.3,
                'ATR 72-600': 2.2,
                'Embraer E190': 3.0,
                'Airbus A220-300': 2.8,
            }.get(aircraft, 3.2)  # Default value if aircraft not in dict
            
            # Adjust consumption based on distance (long flights are more fuel efficient per km)
            if distance_km > 5000:
                base_consumption *= 0.9
            elif distance_km < 1000:
                base_consumption *= 1.1
                
            fuel_consumption_kg = round(distance_km * base_consumption)
            
            # Create the new route
            FlightRoute.objects.create(
                origin=origin,
                destination=destination,
                aircraft_type=aircraft,
                distance_km=distance_km,
                fuel_consumption_kg=fuel_consumption_kg
            )
            new_routes += 1
            
            self.stdout.write(f'Created route: {origin} → {destination} ({aircraft})')
        
        self.stdout.write(self.style.SUCCESS(
            f'Route generation complete: {existing_routes} existing, {new_routes} new, {skipped_routes} skipped'
        ))
