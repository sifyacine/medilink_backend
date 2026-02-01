"""
WebSocket authentication middleware.

Provides JWT token authentication for WebSocket connections.
Tokens can be passed via:
1. Query string: ws://example.com/ws/notifications/?token=<jwt_token>
2. Cookie (if using session auth)
"""
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from urllib.parse import parse_qs
import logging

logger = logging.getLogger(__name__)


@database_sync_to_async
def get_user_from_token(token: str):
    """
    Validate JWT token and return user.
    
    Supports both Simple JWT and Django REST Knox tokens.
    """
    if not token:
        return AnonymousUser()
    
    # Try Simple JWT first
    try:
        from rest_framework_simplejwt.tokens import AccessToken
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        access_token = AccessToken(token)
        user_id = access_token.get('user_id')
        
        if user_id:
            try:
                return User.objects.get(id=user_id)
            except User.DoesNotExist:
                logger.warning(f"User {user_id} not found for JWT token")
                return AnonymousUser()
    except ImportError:
        pass  # Simple JWT not installed
    except Exception as e:
        logger.debug(f"JWT token validation failed: {e}")
    
    # Try Knox token
    try:
        from knox.auth import TokenAuthentication
        from django.http import HttpRequest
        
        knox_auth = TokenAuthentication()
        # Knox expects "Token <token>" format
        user, _ = knox_auth.authenticate_credentials(token.encode())
        if user:
            return user
    except ImportError:
        pass  # Knox not installed
    except Exception as e:
        logger.debug(f"Knox token validation failed: {e}")
    
    # Try DRF authtoken
    try:
        from rest_framework.authtoken.models import Token
        
        token_obj = Token.objects.select_related('user').get(key=token)
        return token_obj.user
    except ImportError:
        pass  # DRF authtoken not installed
    except Exception as e:
        logger.debug(f"DRF authtoken validation failed: {e}")
    
    return AnonymousUser()


class WebSocketJWTAuthMiddleware(BaseMiddleware):
    """
    WebSocket middleware for JWT/Token authentication.
    
    Usage in ASGI config:
        from notifications.middleware import WebSocketJWTAuthMiddleware
        
        application = ProtocolTypeRouter({
            "websocket": WebSocketJWTAuthMiddleware(
                URLRouter(websocket_urlpatterns)
            ),
        })
    
    Token can be passed via query string:
        ws://example.com/ws/notifications/?token=<your_jwt_token>
    """
    
    async def __call__(self, scope, receive, send):
        # Try to get token from query string
        query_string = scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)
        
        token = None
        
        # Check for token in query params
        if 'token' in query_params:
            token = query_params['token'][0]
        
        # If no token in query, check cookies
        if not token:
            headers = dict(scope.get('headers', []))
            cookie_header = headers.get(b'cookie', b'').decode()
            
            # Parse cookies
            cookies = {}
            for cookie in cookie_header.split('; '):
                if '=' in cookie:
                    key, value = cookie.split('=', 1)
                    cookies[key] = value
            
            # Try to get token from cookie
            token = cookies.get('access_token') or cookies.get('auth_token')
        
        # Authenticate user
        if token:
            scope['user'] = await get_user_from_token(token)
        else:
            # Fall back to session auth (already handled by AuthMiddlewareStack)
            if 'user' not in scope or scope['user'] is None:
                scope['user'] = AnonymousUser()
        
        return await super().__call__(scope, receive, send)


class WebSocketAuthMiddlewareStack:
    """
    Convenience wrapper that combines JWT auth with session auth.
    
    Usage:
        from notifications.middleware import WebSocketAuthMiddlewareStack
        
        application = ProtocolTypeRouter({
            "websocket": WebSocketAuthMiddlewareStack(
                URLRouter(websocket_urlpatterns)
            ),
        })
    """
    
    def __new__(cls, inner):
        from channels.auth import AuthMiddlewareStack
        return WebSocketJWTAuthMiddleware(AuthMiddlewareStack(inner))
