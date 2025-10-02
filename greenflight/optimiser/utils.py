"""
Utility functions for flight emission calculations.
"""

# Default emission factors
DEFAULT_CO2_PER_KG_FUEL = 3.15  # kg CO2 per kg of aviation fuel
DEFAULT_FUEL_DENSITY = 0.8  # kg per liter (typical for Jet A-1)
DEFAULT_CO2_PER_PASSENGER_KM = 0.09  # kg CO2 per passenger-km (simple default)
DEFAULT_PASSENGERS = 150


def estimate_emissions(distance_km, fuel_burn_per_km, passengers=DEFAULT_PASSENGERS, 
                      co2_per_kg_fuel=DEFAULT_CO2_PER_KG_FUEL, 
                      fuel_density=DEFAULT_FUEL_DENSITY,
                      use_simple_method=False):
    """
    Calculate fuel consumption and CO2 emissions for a flight.
    
    Args:
        distance_km (float): Flight distance in kilometers
        fuel_burn_per_km (float): Fuel consumption in liters per km
        passengers (int): Number of passengers (default: 150)
        co2_per_kg_fuel (float): CO2 emission factor in kg per kg fuel (default: 3.15)
        fuel_density (float): Fuel density in kg/liter (default: 0.8)
        use_simple_method (bool): Use simple passenger-km method instead of fuel-based
        
    Returns:
        tuple: (fuel_liters, co2_kg) - total fuel consumption and CO2 emissions
    """
    if use_simple_method:
        # Simple method: CO2 per passenger-km
        total_co2_kg = distance_km * passengers * DEFAULT_CO2_PER_PASSENGER_KM
        # Estimate fuel from CO2 (reverse calculation)
        fuel_kg = total_co2_kg / co2_per_kg_fuel
        fuel_liters = fuel_kg / fuel_density
    else:
        # Detailed method: based on actual fuel consumption
        fuel_liters = distance_km * fuel_burn_per_km
        fuel_kg = fuel_liters * fuel_density
        total_co2_kg = fuel_kg * co2_per_kg_fuel
    
    return round(fuel_liters, 2), round(total_co2_kg, 2)


def calculate_per_passenger_emissions(distance_km, fuel_burn_per_km, passengers=DEFAULT_PASSENGERS,
                                    **kwargs):
    """
    Calculate emissions per passenger for a flight.
    
    Returns:
        tuple: (fuel_per_passenger, co2_per_passenger)
    """
    fuel_liters, co2_kg = estimate_emissions(distance_km, fuel_burn_per_km, passengers, **kwargs)
    
    fuel_per_passenger = fuel_liters / passengers
    co2_per_passenger = co2_kg / passengers
    
    return round(fuel_per_passenger, 3), round(co2_per_passenger, 3)


def compare_aircraft_efficiency(routes_data):
    """
    Compare efficiency of different aircraft on similar routes.
    
    Args:
        routes_data (list): List of dicts with route information
        
    Returns:
        list: Sorted list of routes by efficiency (CO2 per passenger per km)
    """
    efficiency_data = []
    
    for route in routes_data:
        fuel_liters, co2_kg = estimate_emissions(
            route['distance_km'], 
            route['fuel_burn_per_km'],
            route.get('passengers', DEFAULT_PASSENGERS)
        )
        
        co2_per_passenger_km = co2_kg / (route.get('passengers', DEFAULT_PASSENGERS) * route['distance_km'])
        
        efficiency_data.append({
            'route': f"{route['origin']} → {route['destination']}",
            'aircraft_type': route['aircraft_type'],
            'co2_per_passenger_km': round(co2_per_passenger_km, 4),
            'total_co2_kg': co2_kg,
            'fuel_liters': fuel_liters
        })
    
    return sorted(efficiency_data, key=lambda x: x['co2_per_passenger_km'])
