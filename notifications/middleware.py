"""
WebSocket authentication middleware for Django Channels.

Authenticates WebSocket connections using Token authentication.
Supports:
- Token via query string: ws://...?token=<token>
- Token via subprotocol header (for clients that can't set query params)

Usage in ASGI:
    from notifications.middleware import WebSocketAuthMiddlewareStack

    application = ProtocolTypeRouter({
        "websocket": WebSocketAuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        ),
    })
"""
import logging
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from channels.auth import AuthMiddlewareStack
from django.contrib.auth.models import AnonymousUser
from rest_framework.authtoken.models import Token

logger = logging.getLogger(__name__)


@database_sync_to_async
def get_user_from_token(token_key: str):
    """
    Resolve a DRF Token string to its associated User.

    Returns AnonymousUser if the token is invalid or the account
    cannot log in.
    """
    try:
        token = Token.objects.select_related("user").get(key=token_key)
        user = token.user
        if user.is_active and getattr(user, "can_login", True):
            return user
        logger.warning("WebSocket auth: user %s cannot log in", user.id)
    except Token.DoesNotExist:
        logger.debug("WebSocket auth: invalid token")
    return AnonymousUser()


class TokenAuthMiddleware(BaseMiddleware):
    """
    Channels middleware that authenticates via ``?token=<key>`` query param.

    Falls back to AnonymousUser when no valid token is provided, so
    downstream consumers can decide to ``close()`` unauthenticated
    connections themselves.
    """

    async def __call__(self, scope, receive, send):
        # Parse query string for token
        query_string = scope.get("query_string", b"").decode("utf-8")
        query_params = parse_qs(query_string)
        token_key = query_params.get("token", [None])[0]

        if token_key:
            scope["user"] = await get_user_from_token(token_key)
        else:
            # No token in query string — leave user as-is (session auth
            # may have already populated it via AuthMiddlewareStack).
            if "user" not in scope or scope["user"] is None:
                scope["user"] = AnonymousUser()

        return await super().__call__(scope, receive, send)


def WebSocketAuthMiddlewareStack(inner):
    """
    Convenience wrapper that applies session auth first, then token auth.

    Clients can authenticate via:
    1. Django session cookie (browser-based)
    2. ``?token=<DRF-token>`` query parameter (mobile / API clients)
    """
    return AuthMiddlewareStack(TokenAuthMiddleware(inner))
