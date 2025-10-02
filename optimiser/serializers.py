from rest_framework import serializers
from .models import FlightRoute, EmissionRecord, PassengerEcoScore

class FlightRouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = FlightRoute
        fields = ['id', 'origin', 'destination', 'aircraft_type', 'distance_km', 'fuel_consumption_kg']

class EmissionRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmissionRecord
        fields = ['id', 'route', 'calculation_date', 'co2_kg', 'fuel_saved_kg', 'percent_improvement']

class PassengerEcoScoreSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = PassengerEcoScore
        fields = ['id', 'username', 'points', 'flights_optimized', 'total_co2_saved', 'current_badge']

class OptimiseFlightSerializer(serializers.Serializer):
    origin = serializers.CharField(max_length=100)
    destination = serializers.CharField(max_length=100)
    aircraft_type = serializers.CharField(max_length=100)
