from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import json
from .models import FlightRoute, PassengerEcoScore, EmissionRecord
from .serializers import FlightRouteSerializer, PassengerEcoScoreSerializer
from .utils import estimate_emissions, calculate_per_passenger_emissions
from rest_framework.views import APIView
from rest_framework.response import Response

# Create your views here.

def home_view(request):
    """Render the home template"""
    return render(request, 'optimiser/home.html')


def health_check_view(request):
    """Basic health check endpoint"""
    return JsonResponse({'status': 'healthy'}, status=200)


def optimise_flight_view(request):
    """
    POST /api/optimise-flight/
    Accepts origin, destination, aircraft_type and returns optimized emissions data
    """
    if request.method == 'POST':
        data = json.loads(request.body)
        origin = data.get('origin')
        destination = data.get('destination')
        aircraft_type = data.get('aircraft_type')
        
        if not all([origin, destination, aircraft_type]):
            return JsonResponse(
                {'error': 'origin, destination, and aircraft_type are required'}, 
                status=400
            )
        
        try:
            # Find the requested route
            route = FlightRoute.objects.get(
                origin__iexact=origin,
                destination__iexact=destination,
                aircraft_type__iexact=aircraft_type
            )
            
            # Calculate original emissions
            original_fuel, original_co2 = estimate_emissions(
                route.distance_km, 
                route.fuel_burn_per_km
            )
            
            # Find more efficient alternatives (same route, different aircraft)
            alternative_routes = FlightRoute.objects.filter(
                origin__iexact=origin,
                destination__iexact=destination
            ).exclude(id=route.id)
            
            best_alternative = None
            best_fuel = original_fuel
            best_co2 = original_co2
            
            for alt_route in alternative_routes:
                alt_fuel, alt_co2 = estimate_emissions(
                    alt_route.distance_km,
                    alt_route.fuel_burn_per_km
                )
                if alt_co2 < best_co2:
                    best_alternative = alt_route
                    best_fuel = alt_fuel
                    best_co2 = alt_co2
            
            # If no better alternative found, apply 10% optimization factor
            if not best_alternative:
                optimized_fuel = original_fuel * 0.9  # 10% fuel savings
                optimized_co2 = original_co2 * 0.9
            else:
                optimized_fuel = best_fuel
                optimized_co2 = best_co2
            
            fuel_saved = original_fuel - optimized_fuel
            co2_saved = original_co2 - optimized_co2
            
            return JsonResponse({
                'route': f"{route.origin} → {route.destination}",
                'original': {
                    'aircraft_type': route.aircraft_type,
                    'fuel': original_fuel,
                    'co2': original_co2
                },
                'optimised': {
                    'aircraft_type': best_alternative.aircraft_type if best_alternative else route.aircraft_type,
                    'fuel': round(optimized_fuel, 2),
                    'co2': round(optimized_co2, 2)
                },
                'fuel_saved': round(fuel_saved, 2),
                'co2_saved': round(co2_saved, 2),
                'savings_percentage': round((co2_saved / original_co2) * 100, 1) if original_co2 > 0 else 0
            })
            
        except FlightRoute.DoesNotExist:
            return JsonResponse(
                {'error': f'Route not found: {origin} → {destination} with {aircraft_type}'}, 
                status=404
            )
        except Exception as e:
            return JsonResponse(
                {'error': f'Calculation error: {str(e)}'}, 
                status=500
            )
    return JsonResponse({'error': 'Method not allowed'}, status=405)


def route_list_view(request):
    """
    GET /api/routes/
    List all available flight routes
    """
    queryset = FlightRoute.objects.all()
    serializer = FlightRouteSerializer(queryset, many=True)
    return JsonResponse(serializer.data, safe=False)


def passenger_score_view(request):
    """
    GET /api/passenger-score/?user_name=
    Returns eco-score and badges for a specific user
    """
    user_name = request.GET.get('user_name')
    
    if not user_name:
        return JsonResponse(
            {'error': 'user_name parameter is required'}, 
            status=400
        )
    
    try:
        passenger_score = PassengerEcoScore.objects.get(
            user_name__iexact=user_name.strip()
        )
        
        serializer = PassengerEcoScoreSerializer(passenger_score)
        return JsonResponse(serializer.data)
        
    except PassengerEcoScore.DoesNotExist:
        return JsonResponse(
            {'error': 'Passenger eco-score not found'}, 
            status=404
        )
    except Exception as e:
        return JsonResponse(
            {'error': f'Error retrieving passenger score: {str(e)}'}, 
            status=500
        )


def index(request):
    """Render the main optimization page"""
    return render(request, 'optimiser/index.html')

@csrf_exempt
def optimize_flight(request):
    """Handle flight optimization requests"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            origin = data.get('origin', '').strip()
            destination = data.get('destination', '').strip()
            aircraft_type = data.get('aircraft_type', '').strip()
            
            if not all([origin, destination, aircraft_type]):
                return JsonResponse({
                    'success': False,
                    'error': 'Missing required fields'
                }, status=400)
            
            # Get or create the flight route
            route = FlightRoute.get_or_calculate_route(origin, destination, aircraft_type)
            
            # Calculate emissions
            co2_emissions = route.calculate_co2_emissions()
            
            # Create emission record
            EmissionRecord.objects.create(
                flight=route,
                co2_kg=co2_emissions,
                fuel_saved_liters=0.0  # Implement optimization logic here
            )
            
            return JsonResponse({
                'success': True,
                'route': {
                    'origin': route.origin,
                    'destination': route.destination,
                    'aircraft_type': route.aircraft_type,
                    'distance_km': route.distance_km,
                    'co2_kg': co2_emissions,
                    'fuel_burn_per_km': route.fuel_burn_per_km
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

class FlightRouteAPI(APIView):
    """API for flight route operations"""
    
    def get(self, request):
        """Get all flight routes"""
        routes = FlightRoute.objects.all()
        data = [{
            'id': route.id,
            'origin': route.origin,
            'destination': route.destination,
            'aircraft_type': route.aircraft_type,
            'distance_km': route.distance_km,
            'fuel_burn_per_km': route.fuel_burn_per_km
        } for route in routes]
        
        return Response({
            'success': True,
            'routes': data
        })

def home(request):
    """Home page view"""
    return HttpResponse("<h1>Welcome to GreenFlight Optimizer</h1><p>This is a platform to optimize flight routes for reduced carbon emissions.</p>")
