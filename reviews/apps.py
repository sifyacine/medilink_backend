"""Reviews app configuration."""
from django.apps import AppConfig


class ReviewsConfig(AppConfig):
    """Configuration for the reviews app."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reviews'
    verbose_name = 'Reviews & Ratings'
    
    def ready(self):
        """Import signals when app is ready."""
        try:
            import reviews.signals  # noqa: F401
        except ImportError:
            pass
