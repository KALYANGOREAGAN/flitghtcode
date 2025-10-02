from django.db import models
from django.utils import timezone
import math


class FlightRoute(models.Model):
    origin = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    distance_km = models.FloatField()
    aircraft_type = models.CharField(max_length=50)
    fuel_burn_per_km = models.FloatField(help_text="Fuel consumption in liters per km")
    
    def __str__(self):
        return f"{self.origin} → {self.destination} ({self.aircraft_type})"
    
    class Meta:
        unique_together = ['origin', 'destination', 'aircraft_type']
    
    @classmethod
    def get_or_calculate_route(cls, origin, destination, aircraft_type):
        """Get existing route or calculate a new one"""
        try:
            return cls.objects.get(
                origin__iexact=origin,
                destination__iexact=destination,
                aircraft_type__iexact=aircraft_type
            )
        except cls.DoesNotExist:
            # Try to find a route with any aircraft type first
            try:
                similar_route = cls.objects.filter(
                    origin__iexact=origin,
                    destination__iexact=destination
                ).first()
                
                if similar_route:
                    # Use distance from similar route but different fuel burn
                    distance = similar_route.distance_km
                else:
                    # Calculate distance if no similar route exists
                    distance = cls.calculate_distance(origin, destination)
                
                fuel_burn = cls.get_aircraft_fuel_burn(aircraft_type)
                
                return cls.objects.create(
                    origin=origin.title(),
                    destination=destination.title(),
                    distance_km=distance,
                    aircraft_type=aircraft_type,
                    fuel_burn_per_km=fuel_burn
                )
            except Exception as e:
                # Log the error and create with defaults
                print(f"Error creating route: {e}")
                return cls.objects.create(
                    origin=origin.title(),
                    destination=destination.title(),
                    distance_km=1000.0,  # Default distance
                    aircraft_type=aircraft_type,
                    fuel_burn_per_km=cls.get_aircraft_fuel_burn(aircraft_type)
                )
    
    @staticmethod
    def calculate_distance(origin, destination):
        """Calculate approximate distance between airports (placeholder)"""
        # This is a simplified calculation - in production you'd use actual airport coordinates
        airport_coords = {
            'entebbe': (0.0424, 32.4435),
            'nairobi': (-1.3192, 36.9276),
            # Add more airports as needed
        }
        
        if origin.lower() in airport_coords and destination.lower() in airport_coords:
            lat1, lon1 = airport_coords[origin.lower()]
            lat2, lon2 = airport_coords[destination.lower()]
            
            # Haversine formula for great circle distance
            R = 6371  # Earth's radius in km
            dlat = math.radians(lat2 - lat1)
            dlon = math.radians(lon2 - lon1)
            a = (math.sin(dlat/2)**2 + 
                 math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
                 math.sin(dlon/2)**2)
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            return R * c
        
        return 1000.0  # Default fallback distance
    
    @staticmethod
    def get_aircraft_fuel_burn(aircraft_type):
        """Get fuel burn rate for aircraft type"""
        fuel_burns = {
            'airbus a319': 2.5,
            'a319': 2.5,
            'boeing 737': 2.8,
            'b737': 2.8,
            # Add more aircraft types
        }
        return fuel_burns.get(aircraft_type.lower(), 3.0)  # Default fuel burn
    
    def calculate_co2_emissions(self):
        """Calculate CO2 emissions for this route"""
        # 1 liter of jet fuel produces approximately 2.52 kg of CO2
        total_fuel = self.distance_km * self.fuel_burn_per_km
        return total_fuel * 2.52


class EmissionRecord(models.Model):
    flight = models.ForeignKey(FlightRoute, on_delete=models.CASCADE, related_name='emission_records')
    co2_kg = models.FloatField(help_text="CO2 emissions in kilograms")
    fuel_saved_liters = models.FloatField(default=0.0, help_text="Fuel saved in liters")
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"Emission for {self.flight} - {self.co2_kg}kg CO2"
    
    class Meta:
        ordering = ['-created_at']


class PassengerEcoScore(models.Model):
    user_name = models.CharField(max_length=100, unique=True)
    points = models.IntegerField(default=0)
    badges = models.TextField(blank=True, help_text="Comma-separated list of badges")
    
    def __str__(self):
        return f"{self.user_name} - {self.points} points"
    
    def get_badges_list(self):
        """Return badges as a list"""
        if self.badges:
            return [badge.strip() for badge in self.badges.split(',')]
        return []
    
    def add_badge(self, badge):
        """Add a new badge if not already present"""
        badges_list = self.get_badges_list()
        if badge not in badges_list:
            badges_list.append(badge)
            self.badges = ', '.join(badges_list)
    
    class Meta:
        ordering = ['-points']
