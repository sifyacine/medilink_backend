from django.apps import AppConfig
import os
import logging

logger = logging.getLogger(__name__)


class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notifications'

    def ready(self):
        """Initialize Firebase Admin SDK when Django starts"""
        import firebase_admin
        from firebase_admin import credentials
        from django.conf import settings

        # Only initialize if not already initialized
        if not firebase_admin._apps:
            try:
                # Get credentials path from settings or environment
                cred_path = getattr(
                    settings, 
                    'FIREBASE_CREDENTIALS_PATH', 
                    os.environ.get('FIREBASE_CREDENTIALS_PATH', 'firebase-credentials.json')
                )
                
                # Make path absolute if relative
                if not os.path.isabs(cred_path):
                    cred_path = os.path.join(settings.BASE_DIR, cred_path)
                
                if os.path.exists(cred_path):
                    cred = credentials.Certificate(cred_path)
                    firebase_admin.initialize_app(cred)
                    logger.info("✅ Firebase Admin SDK initialized successfully")
                else:
                    logger.warning(
                        f"⚠️ Firebase credentials file not found at: {cred_path}. "
                        "FCM notifications will not work. "
                        "Download from Firebase Console > Project Settings > Service Accounts"
                    )
            except Exception as e:
                logger.error(f"❌ Failed to initialize Firebase Admin SDK: {e}")
