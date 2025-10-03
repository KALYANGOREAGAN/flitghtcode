from django.core.management.base import BaseCommand
from optimiser.models import FlightRoute
from django.db import transaction

class Command(BaseCommand):
    help = 'Create sample data with various routes for development and testing'

    def handle(self, *args, **options):
        # Sample data with direct routes
        routes = [
            # Africa routes
            {'origin': 'NAIROBI', 'destination': 'ENTEBBE', 'aircraft_type': 'Boeing 737-800', 'distance_km': 500, 'fuel_consumption_kg': 1800},
            {'origin': 'NAIROBI', 'destination': 'ENTEBBE', 'aircraft_type': 'Airbus A320', 'distance_km': 500, 'fuel_consumption_kg': 1750},
            {'origin': 'NAIROBI', 'destination': 'ENTEBBE', 'aircraft_type': 'Embraer E190', 'distance_km': 500, 'fuel_consumption_kg': 1550},
            
            # Europe routes
            {'origin': 'LONDON', 'destination': 'PARIS', 'aircraft_type': 'Boeing 737-800', 'distance_km': 340, 'fuel_consumption_kg': 1350},
            {'origin': 'LONDON', 'destination': 'PARIS', 'aircraft_type': 'Airbus A320', 'distance_km': 340, 'fuel_consumption_kg': 1300},
            {'origin': 'LONDON', 'destination': 'BERLIN', 'aircraft_type': 'Boeing 737-800', 'distance_km': 930, 'fuel_consumption_kg': 3200},
            
            # North America routes
            {'origin': 'NEW YORK', 'destination': 'WASHINGTON', 'aircraft_type': 'Boeing 737-800', 'distance_km': 330, 'fuel_consumption_kg': 1200},
            {'origin': 'NEW YORK', 'destination': 'WASHINGTON', 'aircraft_type': 'Embraer E190', 'distance_km': 330, 'fuel_consumption_kg': 1100},
            
            # Intercontinental routes
            {'origin': 'LONDON', 'destination': 'NEW YORK', 'aircraft_type': 'Boeing 777-300ER', 'distance_km': 5550, 'fuel_consumption_kg': 18500},
            {'origin': 'LONDON', 'destination': 'NEW YORK', 'aircraft_type': 'Boeing 787-9', 'distance_km': 5550, 'fuel_consumption_kg': 16800},
            {'origin': 'LONDON', 'destination': 'NEW YORK', 'aircraft_type': 'Airbus A350-900', 'distance_km': 5550, 'fuel_consumption_kg': 16500},
            
            # New routes with new cities/aircraft
            {'origin': 'DUBAI', 'destination': 'BANGKOK', 'aircraft_type': 'Boeing 777-300ER', 'distance_km': 4890, 'fuel_consumption_kg': 17200},
            {'origin': 'SINGAPORE', 'destination': 'TOKYO', 'aircraft_type': 'Airbus A350-900', 'distance_km': 5300, 'fuel_consumption_kg': 15400},
            {'origin': 'LOS ANGELES', 'destination': 'TOKYO', 'aircraft_type': 'Boeing 787-9', 'distance_km': 8800, 'fuel_consumption_kg': 25600},
            {'origin': 'SYDNEY', 'destination': 'SINGAPORE', 'aircraft_type': 'Airbus A380', 'distance_km': 6300, 'fuel_consumption_kg': 29500},
        ]

        with transaction.atomic():
            # Clear existing routes if needed
            if options.get('clear', False):
                FlightRoute.objects.all().delete()
                self.stdout.write("Cleared existing routes")

            # Create the routes
            created = 0
            for route_data in routes:
                # Check if the route already exists
                exists = FlightRoute.objects.filter(
                    origin=route_data['origin'],
                    destination=route_data['destination'],
                    aircraft_type=route_data['aircraft_type']
                ).exists()
                
                if not exists:
                    FlightRoute.objects.create(**route_data)
                    created += 1
                    self.stdout.write(f"Created route: {route_data['origin']} → {route_data['destination']} ({route_data['aircraft_type']})")
            
            self.stdout.write(self.style.SUCCESS(f"Created {created} new routes"))

        # Suggest next steps
        self.stdout.write("\nSample data created. You can now:")
        self.stdout.write(" - Run 'python manage.py ensure_all_routes' to create all combinations")
        self.stdout.write(" - Visit the web interface to optimize these routes")
