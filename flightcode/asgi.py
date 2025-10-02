"""
ASGI config for flightcode project.
"""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flightcode.settings')
application = get_asgi_application()
