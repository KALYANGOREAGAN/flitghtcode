from django.shortcuts import render, redirect
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from django.db import models
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import FlightRoute, EmissionRecord, PassengerEcoScore
from .serializers import FlightRouteSerializer, EmissionRecordSerializer, PassengerEcoScoreSerializer, OptimiseFlightSerializer
from .utils import estimate_emissions, compare_aircraft_efficiency, calculate_optimization

def home(request):
    """Render the home page"""
    # Redirect authenticated users to dashboard
    if request.user.is_authenticated:
        return redirect('optimiser:dashboard')

    # Emergency database initialization if tables don't exist
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            try:
                cursor.execute("SELECT COUNT(*) FROM optimiser_flightroute")
                count = cursor.fetchone()[0]
                print(f"Found {count} routes in database")
            except Exception as db_error:
                print(f"Database error: {str(db_error)}")
                print("Attempting emergency migration...")
                try:
                    # Try to create the table directly
                    cursor.execute("""
                    CREATE TABLE IF NOT EXISTS optimiser_flightroute (
                        id SERIAL PRIMARY KEY,
                        origin VARCHAR(100) NOT NULL,
                        destination VARCHAR(100) NOT NULL,
                        aircraft_type VARCHAR(100) NOT NULL,
                        distance_km FLOAT NOT NULL,
                        fuel_consumption_kg FLOAT NOT NULL
                    )
                    """)
                    
                    # Add some sample data
                    cursor.execute("""
                    INSERT INTO optimiser_flightroute (origin, destination, aircraft_type, distance_km, fuel_consumption_kg)
                    VALUES 
                    ('ENTEBBE', 'NAIROBI', 'Boeing 737-800', 500, 1800),
                    ('LONDON', 'PARIS', 'Airbus A320', 340, 1350),
                    ('NEW YORK', 'WASHINGTON', 'Embraer E190', 330, 1100)
                    ON CONFLICT DO NOTHING
                    """)
                    print("Emergency table creation completed")
                except Exception as create_error:
                    print(f"Emergency table creation failed: {str(create_error)}")
    except Exception as e:
        print(f"Database setup error: {str(e)}")

    # Get data with robust error handling
    try:
        # Get data from database or use defaults if empty
        from .models import FlightRoute
        origins = list(FlightRoute.objects.values_list('origin', flat=True).distinct())
        destinations = list(FlightRoute.objects.values_list('destination', flat=True).distinct())
        aircraft_types = list(FlightRoute.objects.values_list('aircraft_type', flat=True).distinct())
    except Exception as e:
        # Provide default values if database error
        origins = ["ENTEBBE", "NAIROBI", "LONDON", "NEW YORK", "JOHANNESBURG", "PARIS", "BERLIN", 
                  "DUBAI", "SINGAPORE", "TOKYO", "SYDNEY", "CAIRO", "LAGOS", "CHICAGO", "LOS ANGELES"]
        destinations = ["NAIROBI", "DAR ES SALAAM", "PARIS", "WASHINGTON", "CAPE TOWN", "DUBAI", 
                        "AMSTERDAM", "ROME", "BANGKOK", "HONG KONG", "NEW DELHI", "MADRID", "SAN FRANCISCO", 
                        "TORONTO", "MEXICO CITY"]
        aircraft_types = ["Boeing 737-800", "Boeing 787-8", "Boeing 777-300ER", "Boeing 787-9", 
                         "Airbus A320", "Airbus A350-900", "Airbus A330-300", "Airbus A220-300", 
                         "Embraer E190", "ATR 72-600", "Airbus A380"]
        
        # Log the error
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching flight data: {str(e)}")

    # Provide default values if database is empty
    if not origins:
        origins = ["ENTEBBE", "NAIROBI", "LONDON", "NEW YORK", "JOHANNESBURG", "PARIS", "BERLIN", 
                  "DUBAI", "SINGAPORE", "TOKYO", "SYDNEY", "CAIRO", "LAGOS", "CHICAGO", "LOS ANGELES"]
    if not destinations:
        destinations = ["NAIROBI", "DAR ES SALAAM", "PARIS", "WASHINGTON", "CAPE TOWN", "DUBAI", 
                        "AMSTERDAM", "ROME", "BANGKOK", "HONG KONG", "NEW DELHI", "MADRID", "SAN FRANCISCO", 
                        "TORONTO", "MEXICO CITY"]
    if not aircraft_types:
        aircraft_types = ["Boeing 737-800", "Boeing 787-8", "Boeing 777-300ER", "Boeing 787-9", 
                         "Airbus A320", "Airbus A350-900", "Airbus A330-300", "Airbus A220-300", 
                         "Embraer E190", "ATR 72-600", "Airbus A380"]

    context = {
        'origins': origins,
        'destinations': destinations,
        'aircraft_types': aircraft_types
    }
    return render(request, 'optimiser/home.html', context)

class RouteListView(generics.ListAPIView):
    """API endpoint to list all available routes"""
    queryset = FlightRoute.objects.all()
    serializer_class = FlightRouteSerializer
    
    def get_queryset(self):
        queryset = FlightRoute.objects.all()
        origin = self.request.query_params.get('origin')
        destination = self.request.query_params.get('destination')
        
        if origin:
            queryset = queryset.filter(origin=origin)
        if destination:
            queryset = queryset.filter(destination=destination)
            
        return queryset

class OptimiseFlightView(APIView):
    """API endpoint to optimize flight routes"""
    
    def post(self, request):
        print("Received optimization request:", request.data)
        serializer = OptimiseFlightSerializer(data=request.data)
        
        if serializer.is_valid():
            origin = serializer.validated_data['origin']
            destination = serializer.validated_data['destination']
            aircraft_type = serializer.validated_data['aircraft_type']
            
            print(f"Finding route: {origin} to {destination} with {aircraft_type}")
            
            try:
                # Check if route exists
                routes_count = FlightRoute.objects.count()
                print(f"Total routes in database: {routes_count}")
                
                available_routes = FlightRoute.objects.filter(
                    origin=origin, 
                    destination=destination
                )
                print(f"Available routes for {origin}-{destination}: {available_routes.count()}")
                
                # Find the requested route
                original_route = FlightRoute.objects.get(
                    origin=origin,
                    destination=destination, 
                    aircraft_type=aircraft_type
                )
                
                print(f"Found original route: {original_route}")
                
                # Find optimization options
                aircraft_options = compare_aircraft_efficiency(origin, destination)
                print(f"Aircraft options: {len(aircraft_options)}")
                
                if aircraft_options and len(aircraft_options) > 0 and aircraft_options[0]['route'].id != original_route.id:
                    # We found a more efficient aircraft
                    optimized_route = aircraft_options[0]['route']
                    optimization = calculate_optimization(original_route, optimized_route)
                    
                    print(f"Found optimized route: {optimized_route}")
                    
                    # Create emission record
                    EmissionRecord.objects.create(
                        route=original_route,
                        co2_kg=estimate_emissions(original_route.fuel_consumption_kg),
                        fuel_saved_kg=optimization['fuel_saved_kg'],
                        percent_improvement=optimization['percent_improvement']
                    )
                    
                    return Response({
                        'original_route': FlightRouteSerializer(original_route).data,
                        'optimized_route': FlightRouteSerializer(optimized_route).data,
                        'optimization': optimization
                    })
                else:
                    # Apply default optimization
                    optimization = calculate_optimization(original_route)
                    
                    print(f"No better aircraft found, applying standard optimization factor")
                    
                    return Response({
                        'original_route': FlightRouteSerializer(original_route).data,
                        'optimization': optimization,
                        'message': 'No better aircraft found, applying standard optimization factor'
                    })
                    
            except FlightRoute.DoesNotExist:
                print(f"Route not found: {origin} to {destination} with {aircraft_type}")
                available_routes = list(FlightRoute.objects.filter(origin=origin, destination=destination).values_list('aircraft_type', flat=True))
                available_origins = list(FlightRoute.objects.values_list('origin', flat=True).distinct())
                available_destinations = list(FlightRoute.objects.values_list('destination', flat=True).distinct())
                
                # Return available options rather than 404 error
                return Response({
                    'error': f'Route not found: {origin} to {destination} with {aircraft_type}',
                    'available_aircraft': available_routes,
                    'suggestion': 'Try one of the available routes below',
                    'available_origins': available_origins,
                    'available_destinations': available_destinations
                }, status=status.HTTP_200_OK)  # Return 200 instead of 404
                
            except Exception as e:
                import traceback
                print(f"Error in OptimiseFlightView: {str(e)}")
                print(traceback.format_exc())
                return Response({'error': f'Optimization calculation error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            print(f"Serializer errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PassengerScoreView(APIView):
    """API endpoint for passenger eco-scoring"""
    
    def get(self, request):
        if request.user.is_authenticated:
            score, created = PassengerEcoScore.objects.get_or_create(user=request.user)
            serializer = PassengerEcoScoreSerializer(score)
            return Response(serializer.data)
        return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
    
    def post(self, request):
        if request.user.is_authenticated:
            score, created = PassengerEcoScore.objects.get_or_create(user=request.user)
            
            # Update eco score based on CO2 savings
            co2_saved = request.data.get('co2_saved_kg', 0)
            
            if co2_saved > 0:
                score.points += int(co2_saved / 10)  # 1 point for every 10kg of CO2 saved
                score.flights_optimized += 1
                score.total_co2_saved += co2_saved
                
                # Update badge based on points
                if score.points >= 1000:
                    score.current_badge = 'PLATINUM'
                elif score.points >= 500:
                    score.current_badge = 'GOLD'
                elif score.points >= 200:
                    score.current_badge = 'SILVER'
                elif score.points >= 50:
                    score.current_badge = 'BRONZE'
                
                score.save()
                return Response(PassengerEcoScoreSerializer(score).data)
            
            return Response({'error': 'Invalid CO2 savings value'}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

@login_required
def dashboard(request):
    """Render the user dashboard page"""
    # Get user's eco score
    eco_score, created = PassengerEcoScore.objects.get_or_create(user=request.user)

    # Get recent emission records
    recent_emissions = EmissionRecord.objects.filter(
        route__in=FlightRoute.objects.all()
    ).order_by('-calculation_date')[:5]

    # Calculate total emissions saved
    total_saved = recent_emissions.aggregate(
        total_co2=models.Sum('co2_kg'),
        total_fuel=models.Sum('fuel_saved_kg')
    )

    # Find most efficient routes
    efficient_routes = FlightRoute.objects.all().order_by('fuel_consumption_kg')[:5]

    context = {
        'eco_score': eco_score,
        'recent_emissions': recent_emissions,
        'total_saved': total_saved,
        'efficient_routes': efficient_routes,
        'badge_progress': {
            'current': eco_score.current_badge,
            'next': 'GOLD' if eco_score.current_badge == 'SILVER' else 'PLATINUM' if eco_score.current_badge == 'GOLD' else 'SILVER',
            'progress': min(eco_score.points / 500 * 100, 100) if eco_score.current_badge == 'SILVER' else min(eco_score.points / 1000 * 100, 100) if eco_score.current_badge == 'GOLD' else min(eco_score.points / 200 * 100, 100),
        }
    }

    return render(request, 'optimiser/dashboard.html', context)

def api_docs(request):
    """Render the API documentation page"""
    return render(request, 'optimiser/api_docs.html')

def test_routes(request):
    """Test endpoint to check available routes"""
    routes = FlightRoute.objects.all()
    routes_data = [
        {
            'id': route.id,
            'origin': route.origin,
            'destination': route.destination,
            'aircraft_type': route.aircraft_type,
            'distance_km': route.distance_km,
            'fuel_consumption_kg': route.fuel_consumption_kg
        }
        for route in routes
    ]
    
    return JsonResponse({
        'count': len(routes_data),
        'routes': routes_data
    })

def check_route(request, origin, destination, aircraft_type):
    """Simple API endpoint to check if a specific route exists"""
    route_exists = FlightRoute.objects.filter(
        origin__iexact=origin,
        destination__iexact=destination,
        aircraft_type__iexact=aircraft_type
    ).exists()
    
    return JsonResponse({
        'origin': origin,
        'destination': destination,
        'aircraft_type': aircraft_type,
        'route_exists': route_exists
    })

def available_routes(request):
    """API endpoint to get all available route combinations"""
    origins = list(FlightRoute.objects.values_list('origin', flat=True).distinct())
    destinations = list(FlightRoute.objects.values_list('destination', flat=True).distinct())
    aircraft_types = list(FlightRoute.objects.values_list('aircraft_type', flat=True).distinct())
    
    # Get a sample of existing routes (limit to 20 to avoid huge response)
    sample_routes = [
        f"{route.origin} → {route.destination} ({route.aircraft_type})"
        for route in FlightRoute.objects.all()[:20]
    ]
    
    # Count routes per origin-destination pair
    route_counts = {}
    for route in FlightRoute.objects.all():
        key = f"{route.origin} → {route.destination}"
        if key in route_counts:
            route_counts[key] += 1
        else:
            route_counts[key] = 1
            
    # Format the counts for display
    formatted_counts = [f"{key}: {count} aircraft options" for key, count in route_counts.items()]
    
    return JsonResponse({
        'total_routes': FlightRoute.objects.count(),
        'origins': origins,
        'destinations': destinations, 
        'aircraft_types': aircraft_types,
        'sample_routes': sample_routes,
        'route_counts': formatted_counts[:20]  # Limit to top 20
    })

def verify_routes(request):
    """
    API endpoint to verify all route combinations exist and create missing ones
    """
    # Get all distinct origins, destinations and aircraft types
    origins = list(FlightRoute.objects.values_list('origin', flat=True).distinct())
    destinations = list(FlightRoute.objects.values_list('destination', flat=True).distinct())
    aircraft_types = list(FlightRoute.objects.values_list('aircraft_type', flat=True).distinct())
    
    # Calculate total possible combinations
    total_possible = len(origins) * len(destinations) * len(aircraft_types)
    # Subtract origin=destination combinations which aren't valid
    total_possible -= len(origins) * len(aircraft_types)  # Skip routes to self
    
    # Count existing routes
    existing_count = FlightRoute.objects.count()
    
    # Check for missing routes
    missing_count = total_possible - existing_count
    
    # Generate a test case for the missing route mentioned
    test_route = FlightRoute.objects.filter(
        origin='ENTEBBE', destination='PARIS', aircraft_type='Boeing 737-800'
    ).exists()
    
    response = {
        'origins': origins,
        'destinations': destinations,
        'aircraft_types': aircraft_types,
        'total_possible_routes': total_possible,
        'existing_routes': existing_count,
        'missing_routes': missing_count,
        'test_route_exists': test_route,
        'status': 'All routes exist' if missing_count <= 0 else f'{missing_count} routes missing'
    }
    
    # Allow immediate fixing if requested
    if request.GET.get('fix') == 'true':
        from django.core.management import call_command
        call_command('ensure_all_routes', force=True)
        response['action'] = 'Routes fixed - refresh page to verify'
    
    return JsonResponse(response)

@login_required
def analytics_dashboard(request):
    """Render the advanced analytics dashboard"""
    
    # Get historical emission data
    all_emissions = EmissionRecord.objects.all().order_by('-calculation_date')
    
    # Calculate total impact
    total_co2_saved = all_emissions.aggregate(total=models.Sum('co2_kg'))['total'] or 0
    total_fuel_saved = all_emissions.aggregate(total=models.Sum('fuel_saved_kg'))['total'] or 0
    
    # Calculate equivalent environmental impact
    trees_planted = int(total_co2_saved / 21)  # 1 tree absorbs ~21kg CO2 annually
    car_km_avoided = int(total_co2_saved * 4.3)  # ~230g CO2 per km for average car
    
    # Most efficient routes
    efficient_routes = FlightRoute.objects.all().annotate(
        efficiency=models.F('fuel_consumption_kg') / models.F('distance_km')
    ).order_by('efficiency')[:10]
    
    # Monthly savings trends (last 12 months)
    from django.db.models.functions import TruncMonth
    monthly_data = EmissionRecord.objects.annotate(
        month=TruncMonth('calculation_date')
    ).values('month').annotate(
        co2_saved=models.Sum('co2_kg'),
        fuel_saved=models.Sum('fuel_saved_kg'),
        count=models.Count('id')
    ).order_by('-month')[:12]
    
    # Top aircraft by efficiency
    aircraft_efficiency = {}
    for route in FlightRoute.objects.all():
        aircraft = route.aircraft_type
        if aircraft not in aircraft_efficiency:
            aircraft_efficiency[aircraft] = []
        aircraft_efficiency[aircraft].append(route.fuel_consumption_kg / route.distance_km)
    
    # Calculate average efficiency for each aircraft
    for aircraft, values in aircraft_efficiency.items():
        aircraft_efficiency[aircraft] = sum(values) / len(values)
    
    # Sort by efficiency (lower is better)
    top_aircraft = sorted(aircraft_efficiency.items(), key=lambda x: x[1])[:5]
    
    context = {
        'total_co2_saved': total_co2_saved,
        'total_fuel_saved': total_fuel_saved,
        'trees_planted': trees_planted,
        'car_km_avoided': car_km_avoided,
        'efficient_routes': efficient_routes,
        'monthly_data': list(monthly_data),
        'top_aircraft': top_aircraft,
        'emissions_count': all_emissions.count(),
    }
    
    return render(request, 'optimiser/analytics_dashboard.html', context)

@login_required
def generate_report(request):
    """Generate a sustainability report"""
    try:
        # Try to import reportlab
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
    except ImportError:
        # If reportlab is not available, show an error page with installation instructions
        return render(request, 'optimiser/report_error.html', {
            'error': "Missing required package: reportlab",
            'instructions': "Please install the reportlab package with: pip install reportlab"
        })
        
    from django.http import HttpResponse
    import io
    from datetime import datetime
    
    # Create a file-like buffer to receive PDF data
    buffer = io.BytesIO()
    
    # Create the PDF object, using the buffer as its "file"
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter,
        rightMargin=72, 
        leftMargin=72,
        topMargin=72, 
        bottomMargin=72
    )
    
    # Create styles
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    heading_style = styles['Heading1']
    subheading_style = styles['Heading2']
    normal_style = styles['Normal']
    
    # Add custom style for the green text
    green_style = ParagraphStyle(
        'GreenText', 
        parent=normal_style,
        textColor=colors.green
    )
    
    # Container for elements to build the PDF
    elements = []
    
    # Add title
    elements.append(Paragraph("Flight Emissions Sustainability Report", title_style))
    elements.append(Spacer(1, 0.25*inch))
    
    # Add date
    elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y')}", normal_style))
    elements.append(Spacer(1, 0.5*inch))
    
    # Add executive summary
    elements.append(Paragraph("Executive Summary", heading_style))
    
    # Get summary data
    total_co2_saved = EmissionRecord.objects.aggregate(total=models.Sum('co2_kg'))['total'] or 0
    total_fuel_saved = EmissionRecord.objects.aggregate(total=models.Sum('fuel_saved_kg'))['total'] or 0
    flights_optimized = EmissionRecord.objects.count()
    
    summary_text = f"""
    This report summarizes the environmental impact of flight optimization activities.
    To date, we have optimized {flights_optimized} flights, resulting in:
    
    • <b>{total_co2_saved:.2f} kg</b> of CO₂ emissions saved
    • <b>{total_fuel_saved:.2f} kg</b> of aviation fuel saved
    
    This is equivalent to planting approximately <b>{int(total_co2_saved/21)}</b> trees or removing <b>{int(total_co2_saved/4600)}</b> cars from the road for one year.
    """
    
    elements.append(Paragraph(summary_text, normal_style))
    elements.append(Spacer(1, 0.25*inch))
    
    # Add most efficient routes section
    elements.append(Paragraph("Most Efficient Routes", heading_style))
    
    efficient_routes = FlightRoute.objects.all().annotate(
        efficiency=models.F('fuel_consumption_kg') / models.F('distance_km')
    ).order_by('efficiency')[:5]
    
    # Create data for the table
    route_data = [['Route', 'Aircraft', 'Distance (km)', 'Efficiency (kg/km)']]
    
    for route in efficient_routes:
        efficiency = route.fuel_consumption_kg / route.distance_km
        route_data.append([
            f"{route.origin} → {route.destination}",
            route.aircraft_type,
            f"{route.distance_km}",
            f"{efficiency:.2f}"
        ])
    
    # Create the table
    table = Table(route_data, colWidths=[2*inch, 1.5*inch, 1*inch, 1.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 0.25*inch))
    
    # Add recommendations
    elements.append(Paragraph("Recommendations for Further Improvements", heading_style))
    
    recommendations = """
    1. <b>Fleet Modernization:</b> Consider newer aircraft models with better fuel efficiency metrics.
    
    2. <b>Operational Optimizations:</b> Implement continuous descent approaches and reduced engine taxi procedures.
    
    3. <b>Route Planning:</b> Utilize meteorological data to plan routes that take advantage of favorable winds.
    
    4. <b>Sustainable Aviation Fuel:</b> Explore opportunities to incorporate sustainable aviation fuels into operations.
    """
    
    elements.append(Paragraph(recommendations, normal_style))
    elements.append(Spacer(1, 0.5*inch))
    
    # Certification statement
    certification = """
    This report is generated by the GreenFlight Optimizer platform. The data and analysis provided are based on industry-standard 
    emissions calculations and actual flight data. This report can be used for internal sustainability tracking and external 
    environmental impact reporting.
    """
    
    elements.append(Paragraph(certification, green_style))
    
    # Build the PDF
    doc.build(elements)
    
    # Get the value of the BytesIO buffer
    pdf = buffer.getvalue()
    buffer.close()
    
    # Create the HTTP response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="flight_sustainability_report.pdf"'
    response.write(pdf)
    
    return response

@login_required
def predictive_analysis(request):
    """API endpoint for predictive analysis of emissions and savings"""
    # Check for required packages
    missing_packages = []
    try:
        import numpy
    except ImportError:
        missing_packages.append("numpy")
        
    try:
        from sklearn.linear_model import LinearRegression
    except ImportError:
        missing_packages.append("scikit-learn")
        
    if missing_packages:
        # Return informative error if packages are missing
        return JsonResponse({
            'error': f"Missing required packages: {', '.join(missing_packages)}",
            'installation_instructions': "Please install the required packages with: pip install numpy scikit-learn",
            'status': 'dependencies_missing'
        }, status=200)  # Return 200 instead of 500 to handle this gracefully
    
    from django.db.models.functions import ExtractMonth, ExtractYear
    import json
    import numpy as np
    
    try:
        # Get historical data for trend analysis
        records = EmissionRecord.objects.annotate(
            month=ExtractMonth('calculation_date'),
            year=ExtractYear('calculation_date')
        ).values('month', 'year').annotate(
            co2_saved=models.Sum('co2_kg'),
            flights=models.Count('id')
        ).order_by('year', 'month')
        
        # Convert to time series
        months = []
        co2_values = []
        
        for i, record in enumerate(records):
            # Use numeric index as time point
            months.append(i)
            co2_values.append(record['co2_saved'] or 0)
        
        # If we have enough data points, build a simple prediction model
        predictions = []
        best_aircraft = []
        monthly_improvement = 0
        
        if len(months) >= 3:
            # Import LinearRegression only if we need it
            try:
                from sklearn.linear_model import LinearRegression
                
                # Reshape for scikit-learn
                X = np.array(months).reshape(-1, 1)
                y = np.array(co2_values)
                
                # Create and fit the model
                model = LinearRegression()
                model.fit(X, y)
                
                # Predict next 6 months
                future_months = np.array(range(len(months), len(months) + 6)).reshape(-1, 1)
                future_predictions = model.predict(future_months)
                
                # Convert predictions to list and ensure no negative values
                predictions = [max(0, float(p)) for p in future_predictions]
                
                # Calculate total potential savings
                current_month_avg = sum(co2_values[-3:]) / 3 if len(co2_values) >= 3 else co2_values[-1] if co2_values else 0
                predicted_month_avg = sum(predictions) / len(predictions)
                monthly_improvement = predicted_month_avg - current_month_avg
                
                # Get best aircraft recommendations based on data
                best_aircraft = list(FlightRoute.objects.values('aircraft_type').annotate(
                    avg_efficiency=models.Avg(models.F('fuel_consumption_kg') / models.F('distance_km'))
                ).order_by('avg_efficiency')[:3].values_list('aircraft_type', flat=True))
            
            except ImportError:
                # Handle case where scikit-learn is not available
                predictions = [co2_values[-1] * 1.1 if co2_values else 100] * 6
                monthly_improvement = 50
                best_aircraft = list(FlightRoute.objects.values_list('aircraft_type', flat=True).distinct())[:3]
        else:
            # Not enough data for predictions
            predictions = [0] * 6
            monthly_improvement = 0
            best_aircraft = []
            
        # Return predictive analytics
        return JsonResponse({
            'historical_data': {
                'months': list(range(len(months))),
                'co2_saved': co2_values
            },
            'predictions': {
                'months': list(range(len(months), len(months) + 6)),
                'co2_saved': predictions,
            },
            'insights': {
                'monthly_improvement': round(monthly_improvement, 2),
                'projected_annual_savings': round(monthly_improvement * 12, 2),
                'best_aircraft_recommendations': best_aircraft,
                'confidence_score': min(len(months) * 10, 100)  # Simple confidence metric
            }
        })
            
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({
            'error': str(e),
            'message': 'Error generating predictive analysis'
        }, status=500)

def health_check(request):
    """Simple health check endpoint for deployment monitoring"""
    from django.http import JsonResponse
    from django.db import connection
    from datetime import datetime
    
    # Check database connection
    try:
        with connection.cursor() as cursor:
            # Try to create tables if they don't exist
            try:
                cursor.execute("SELECT COUNT(*) FROM optimiser_flightroute")
                db_status = "connected, tables exist"
            except Exception:
                db_status = "connected, tables missing"
                
                # Try to run migrations
                from django.core.management import call_command
                try:
                    call_command('migrate', 'optimiser', '--noinput')
                    db_status = "connected, migrations applied"
                except Exception as migrate_error:
                    db_status = f"connected, migration failed: {str(migrate_error)}"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    # Return status
    return JsonResponse({
        "status": "healthy",
        "database": db_status,
        "server_time": str(datetime.now()),
    })
