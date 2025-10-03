from django.core.management.base import BaseCommand
from optimiser.models import FlightRoute
import itertools

class Command(BaseCommand):
    help = 'Ensure all possible route combinations exist in the database'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Force creation of missing routes')

    def handle(self, *args, **options):
        # Get all distinct origins, destinations and aircraft types
        origins = set(FlightRoute.objects.values_list('origin', flat=True).distinct())
        destinations = set(FlightRoute.objects.values_list('destination', flat=True).distinct())
        aircraft_types = set(FlightRoute.objects.values_list('aircraft_type', flat=True).distinct())
        
        self.stdout.write(f'Found {len(origins)} origins, {len(destinations)} destinations, and {len(aircraft_types)} aircraft types')
        
        # Calculate total possible combinations
        total_possible = len(origins) * len(destinations) * len(aircraft_types)
        # Subtract origin=destination combinations which aren't valid
        total_possible -= len(origins) * len(aircraft_types)  # Skip routes to self
        
        self.stdout.write(f'Total possible valid routes: {total_possible}')
        
        # Count existing routes
        existing_count = FlightRoute.objects.count()
        self.stdout.write(f'Existing routes in database: {existing_count}')
        
        # Check if we need to create routes
        if existing_count >= total_possible and not options['force']:
            self.stdout.write(self.style.SUCCESS('All possible routes already exist in the database!'))
            return
            
        # Distance and fuel consumption mappings
        distance_map = {}
        fuel_consumption_factors = {
            'Boeing 737-800': 3.6,
            'Boeing 737-700': 3.7,
            'Boeing 737-900ER': 3.5,
            'Boeing 787-8': 3.2,
            'Boeing 787-9': 3.1,
            'Boeing 777-300ER': 3.9,
            'Boeing 747-8': 4.5,
            'Boeing 767-300ER': 3.8,
            'Boeing 757-200': 3.7,
            'Airbus A320': 3.5,
            'Airbus A319': 3.6,
            'Airbus A321neo': 3.3,
            'Airbus A330-300': 3.4,
            'Airbus A350-900': 3.0,
            'Airbus A380': 4.7,
            'Airbus A220-300': 2.8,
            'Embraer E190': 3.0,
            'Embraer E195-E2': 2.9,
            'ATR 72-600': 2.3,
            'Bombardier Q400': 2.5,
            'Bombardier CRJ-900': 3.0,
        }
        
        # Build distance map from existing routes
        for route in FlightRoute.objects.all():
            key = (route.origin, route.destination)
            if key not in distance_map:
                distance_map[key] = route.distance_km
                
        # Create a mapping for typical distances
        typical_distances = {
            # Africa-Africa routes
            ('ENTEBBE', 'NAIROBI'): 500,
            ('NAIROBI', 'DAR ES SALAAM'): 430,
            ('JOHANNESBURG', 'CAPE TOWN'): 1270,
            ('ADDIS ABABA', 'NAIROBI'): 1160,
            ('CAIRO', 'ADDIS ABABA'): 2210,
            ('LAGOS', 'ACCRA'): 430,
            ('KHARTOUM', 'ADDIS ABABA'): 1000,
            ('ABIDJAN', 'LAGOS'): 780,
            
            # Europe-Europe routes
            ('LONDON', 'PARIS'): 340,
            ('BERLIN', 'PARIS'): 880,
            ('MADRID', 'ROME'): 1360,
            ('AMSTERDAM', 'LONDON'): 370,
            ('STOCKHOLM', 'BERLIN'): 810,
            ('VIENNA', 'PRAGUE'): 280,
            ('ZURICH', 'FRANKFURT'): 300,
            ('LISBON', 'MADRID'): 510,
            
            # North America routes
            ('NEW YORK', 'WASHINGTON'): 330,
            ('CHICAGO', 'NEW YORK'): 1150,
            ('LOS ANGELES', 'SAN FRANCISCO'): 550,
            ('MIAMI', 'ATLANTA'): 980,
            ('TORONTO', 'NEW YORK'): 550,
            ('MEXICO CITY', 'HOUSTON'): 1200,
            ('VANCOUVER', 'SEATTLE'): 200,
            ('DENVER', 'CHICAGO'): 1460,
            
            # Asia routes
            ('DUBAI', 'MUMBAI'): 1920,
            ('SINGAPORE', 'BANGKOK'): 1420,
            ('TOKYO', 'SEOUL'): 1160,
            ('HONG KONG', 'SHANGHAI'): 1260,
            ('DELHI', 'BANGKOK'): 2950,
            ('BEIJING', 'TOKYO'): 2100,
            ('KUALA LUMPUR', 'SINGAPORE'): 300,
            
            # Intercontinental routes
            ('LONDON', 'NEW YORK'): 5550,
            ('PARIS', 'NEW YORK'): 5850,
            ('LONDON', 'NAIROBI'): 6800,
            ('PARIS', 'NAIROBI'): 6200,
            ('LONDON', 'DAR ES SALAAM'): 7300,
            ('ENTEBBE', 'LONDON'): 6500,
            ('ENTEBBE', 'PARIS'): 5900,
            ('NAIROBI', 'NEW YORK'): 11700,
            ('ENTEBBE', 'NEW YORK'): 11500,
            ('DUBAI', 'LONDON'): 5500,
            ('SINGAPORE', 'LONDON'): 10900,
            ('SYDNEY', 'LOS ANGELES'): 12050,
            ('JOHANNESBURG', 'LONDON'): 9000,
            ('TOKYO', 'SAN FRANCISCO'): 8300,
            ('CAIRO', 'NEW YORK'): 9000,
            ('RIO DE JANEIRO', 'MADRID'): 8400,
            ('MEXICO CITY', 'PARIS'): 9200,
            ('TORONTO', 'DUBAI'): 11200,
            ('BANGKOK', 'FRANKFURT'): 9000,
        }
        
        # Fill the distance map with typical distances
        for (o, d), dist in typical_distances.items():
            key = (o, d)
            if key not in distance_map:
                distance_map[key] = dist
            # Also add reverse direction
            rev_key = (d, o)
            if rev_key not in distance_map:
                distance_map[rev_key] = dist
                
        created_count = 0
        skipped_count = 0
        
        # Create missing routes
        total_combinations = len(origins) * len(destinations) * len(aircraft_types)
        self.stdout.write(f'Processing {total_combinations} possible combinations...')
        
        for origin, destination, aircraft in itertools.product(origins, destinations, aircraft_types):
            # Skip routes to self
            if origin == destination:
                continue
                
            # Check if route already exists
            if FlightRoute.objects.filter(
                origin=origin, destination=destination, aircraft_type=aircraft
            ).exists():
                continue
                
            # Get distance or estimate
            key = (origin, destination)
            if key in distance_map:
                distance_km = distance_map[key]
            else:
                # If we can't determine distance, use a default based on region
                if 'YORK' in origin or 'YORK' in destination:
                    # Transatlantic
                    distance_km = 6000
                elif 'LONDON' in origin or 'LONDON' in destination or 'PARIS' in origin or 'PARIS' in destination:
                    # Europe-related
                    distance_km = 5000
                else:
                    # Default regional
                    distance_km = 1000
                
                # Add to map for future use
                distance_map[key] = distance_km
            
            # Calculate fuel consumption
            fuel_factor = fuel_consumption_factors.get(aircraft, 3.4)  # Default if not known
            
            # Long routes are more fuel efficient per km
            if distance_km > 5000:
                efficiency_factor = 0.9
            elif distance_km < 1000:
                efficiency_factor = 1.1
            else:
                efficiency_factor = 1.0
                
            fuel_consumption_kg = int(round(distance_km * fuel_factor * efficiency_factor, -2))  # Round to nearest 100
            
            # Create route
            FlightRoute.objects.create(
                origin=origin,
                destination=destination,
                aircraft_type=aircraft,
                distance_km=distance_km,
                fuel_consumption_kg=fuel_consumption_kg
            )
            
            created_count += 1
            
            if created_count % 10 == 0:
                self.stdout.write(f'Created {created_count} new routes...')
                
        final_count = FlightRoute.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f'Finished: {created_count} new routes created, {skipped_count} skipped. '
            f'Database now contains {final_count} routes.'
        ))
