from .models import FlightRoute, EmissionRecord

def estimate_emissions(fuel_consumption_kg):
    """
    Calculate CO2 emissions based on fuel consumption
    Using the conversion factor of 3.16 kg CO2 per kg of aviation fuel
    """
    return fuel_consumption_kg * 3.16

def compare_aircraft_efficiency(origin, destination):
    """
    Compare different aircraft types for the same route
    Returns a list of aircraft sorted by efficiency
    """
    routes = FlightRoute.objects.filter(origin=origin, destination=destination)
    
    if not routes.exists():
        return []
    
    aircraft_efficiency = []
    for route in routes:
        emissions = estimate_emissions(route.fuel_consumption_kg)
        aircraft_efficiency.append({
            'aircraft_type': route.aircraft_type,
            'fuel_consumption_kg': route.fuel_consumption_kg,
            'emissions_kg': emissions,
            'route': route
        })
    
    # Sort by fuel consumption (lower is better)
    return sorted(aircraft_efficiency, key=lambda x: x['fuel_consumption_kg'])

def calculate_optimization(route, optimized_route=None):
    """
    Calculate optimization metrics compared to the original route
    If no optimized route is provided, apply a 10% optimization factor
    """
    if optimized_route:
        fuel_saved = route.fuel_consumption_kg - optimized_route.fuel_consumption_kg
        percent_improvement = (fuel_saved / route.fuel_consumption_kg) * 100 if route.fuel_consumption_kg > 0 else 0
    else:
        # Apply default 10% optimization factor
        fuel_saved = route.fuel_consumption_kg * 0.1
        percent_improvement = 10.0
    
    co2_saved = estimate_emissions(fuel_saved)
    
    return {
        'fuel_saved_kg': round(fuel_saved, 2),
        'co2_saved_kg': round(co2_saved, 2),
        'percent_improvement': round(percent_improvement, 2)
    }
