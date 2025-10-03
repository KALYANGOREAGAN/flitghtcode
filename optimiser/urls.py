from django.urls import path
from . import views

app_name = 'optimiser'

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('api/docs/', views.api_docs, name='api_docs'),
    path('api/routes/', views.RouteListView.as_view(), name='route-list'),
    path('api/optimise-flight/', views.OptimiseFlightView.as_view(), name='optimise-flight'),
    path('api/passenger-score/', views.PassengerScoreView.as_view(), name='passenger-score'),
    path('api/check-route/<str:origin>/<str:destination>/<str:aircraft_type>/', views.check_route, name='check-route'),
    path('api/available-routes/', views.available_routes, name='available-routes'),
    path('api/verify-routes/', views.verify_routes, name='verify-routes'),
    path('analytics/', views.analytics_dashboard, name='analytics'),
    path('generate-report/', views.generate_report, name='generate-report'),
    path('api/predictive-analysis/', views.predictive_analysis, name='predictive-analysis'),
    path('health/', views.health_check, name='health_check'),
]


