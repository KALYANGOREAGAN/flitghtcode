from django.db import models
from django.contrib.auth.models import User

class FlightRoute(models.Model):
    origin = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    aircraft_type = models.CharField(max_length=100)
    distance_km = models.FloatField()
    fuel_consumption_kg = models.FloatField()
    
    def __str__(self):
        return f"{self.origin} to {self.destination} via {self.aircraft_type}"
    
    class Meta:
        unique_together = ['origin', 'destination', 'aircraft_type']

class EmissionRecord(models.Model):
    route = models.ForeignKey(FlightRoute, on_delete=models.CASCADE, related_name='emissions')
    calculation_date = models.DateTimeField(auto_now_add=True)
    co2_kg = models.FloatField()
    fuel_saved_kg = models.FloatField(default=0)
    percent_improvement = models.FloatField(default=0)
    
    def __str__(self):
        return f"Emissions for {self.route} on {self.calculation_date.date()}"

class PassengerEcoScore(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    points = models.IntegerField(default=0)
    flights_optimized = models.IntegerField(default=0)
    total_co2_saved = models.FloatField(default=0)
    
    BADGE_CHOICES = [
        ('NONE', 'No Badge'),
        ('BRONZE', 'Bronze Eco-Flyer'),
        ('SILVER', 'Silver Eco-Flyer'),
        ('GOLD', 'Gold Eco-Flyer'),
        ('PLATINUM', 'Platinum Eco-Flyer'),
    ]
    
    current_badge = models.CharField(
        max_length=10,
        choices=BADGE_CHOICES,
        default='NONE'
    )
    
    def __str__(self):
        return f"{self.user.username}'s Eco Score: {self.points} points"
