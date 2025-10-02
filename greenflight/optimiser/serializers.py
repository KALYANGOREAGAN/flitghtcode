from rest_framework import serializers
from .models import FlightRoute, EmissionRecord, PassengerEcoScore


class FlightRouteSerializer(serializers.ModelSerializer):
    """Serializer for FlightRoute model"""
    
    class Meta:
        model = FlightRoute
        fields = ['id', 'origin', 'destination', 'distance_km', 'aircraft_type', 'fuel_burn_per_km']
        
    def validate_distance_km(self, value):
        """Validate that distance is positive"""
        if value <= 0:
            raise serializers.ValidationError("Distance must be greater than 0")
        return value
    
    def validate_fuel_burn_per_km(self, value):
        """Validate that fuel burn rate is positive"""
        if value <= 0:
            raise serializers.ValidationError("Fuel burn per km must be greater than 0")
        return value


class EmissionRecordSerializer(serializers.ModelSerializer):
    """Serializer for EmissionRecord model"""
    flight_details = FlightRouteSerializer(source='flight', read_only=True)
    
    class Meta:
        model = EmissionRecord
        fields = ['id', 'flight', 'flight_details', 'co2_kg', 'fuel_saved_liters', 'created_at']
        read_only_fields = ['created_at']
        
    def validate_co2_kg(self, value):
        """Validate that CO2 emissions are non-negative"""
        if value < 0:
            raise serializers.ValidationError("CO2 emissions cannot be negative")
        return value
    
    def validate_fuel_saved_liters(self, value):
        """Validate that fuel saved is non-negative"""
        if value < 0:
            raise serializers.ValidationError("Fuel saved cannot be negative")
        return value


class PassengerEcoScoreSerializer(serializers.ModelSerializer):
    """Serializer for PassengerEcoScore model"""
    badges_list = serializers.SerializerMethodField()
    
    class Meta:
        model = PassengerEcoScore
        fields = ['id', 'user_name', 'points', 'badges', 'badges_list']
        
    def get_badges_list(self, obj):
        """Return badges as a list for easier frontend consumption"""
        return obj.get_badges_list()
    
    def validate_points(self, value):
        """Validate that points are non-negative"""
        if value < 0:
            raise serializers.ValidationError("Points cannot be negative")
        return value
    
    def validate_user_name(self, value):
        """Validate user name format"""
        if not value.strip():
            raise serializers.ValidationError("User name cannot be empty")
        return value.strip()


class EmissionCalculationSerializer(serializers.Serializer):
    """Serializer for emission calculation requests"""
    distance_km = serializers.FloatField(min_value=0.1)
    fuel_burn_per_km = serializers.FloatField(min_value=0.1)
    passengers = serializers.IntegerField(min_value=1, default=150)
    use_simple_method = serializers.BooleanField(default=False)
