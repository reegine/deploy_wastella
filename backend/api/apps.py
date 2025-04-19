# api/apps.py
from django.apps import AppConfig

class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'  # Ensure this matches the app name

    def ready(self):
        import api.signals  # Import the signals module