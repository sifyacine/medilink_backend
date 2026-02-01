"""
Custom exception handler for consistent API error responses.

Provides:
- Standardized error response format
- Domain exception handling
- Django/DRF exception translation
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404

from common.exceptions import MedilinkException


def medilink_exception_handler(exc, context):
    """
    Custom exception handler for Medilink API.
    
    Provides consistent error response format across all endpoints:
    {
        "success": false,
        "error": "Human-readable error message",
        "code": "error_code",
        "details": { ... }  # Optional additional info
    }
    """
    # Handle Medilink domain exceptions
    if isinstance(exc, MedilinkException):
        return Response(
            exc.to_dict(),
            status=exc.status_code
        )
    
    # Handle Django ValidationError
    if isinstance(exc, DjangoValidationError):
        if hasattr(exc, 'message_dict'):
            # Field-specific errors
            return Response(
                {
                    'success': False,
                    'error': 'Validation failed.',
                    'code': 'validation_error',
                    'details': {'fields': exc.message_dict}
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        else:
            # Single message
            messages = exc.messages if hasattr(exc, 'messages') else [str(exc)]
            return Response(
                {
                    'success': False,
                    'error': '; '.join(messages),
                    'code': 'validation_error',
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
    # Let DRF handle the rest
    response = exception_handler(exc, context)
    
    if response is not None:
        # Standardize DRF error responses
        error_data = {
            'success': False,
            'code': 'error',
        }
        
        # Extract error message
        if isinstance(response.data, dict):
            if 'detail' in response.data:
                error_data['error'] = str(response.data['detail'])
                error_data['code'] = response.data.get('code', 'error')
            elif 'non_field_errors' in response.data:
                error_data['error'] = '; '.join(response.data['non_field_errors'])
                error_data['code'] = 'validation_error'
                error_data['details'] = {'fields': response.data}
            else:
                # Field errors from serializer
                error_data['error'] = 'Validation failed.'
                error_data['code'] = 'validation_error'
                error_data['details'] = {'fields': response.data}
        elif isinstance(response.data, list):
            error_data['error'] = '; '.join(str(e) for e in response.data)
        else:
            error_data['error'] = str(response.data)
        
        response.data = error_data
    
    return response


def get_error_response(message, code='error', status_code=status.HTTP_400_BAD_REQUEST, details=None):
    """
    Helper function to create consistent error responses in views.
    
    Usage:
        return get_error_response("Something went wrong", code="something_error")
    """
    data = {
        'success': False,
        'error': message,
        'code': code,
    }
    if details:
        data['details'] = details
    
    return Response(data, status=status_code)


def get_success_response(data=None, message=None, status_code=status.HTTP_200_OK, **extra):
    """
    Helper function to create consistent success responses in views.
    
    Usage:
        return get_success_response(data=serializer.data, message="Created successfully")
    """
    response_data = {'success': True}
    if message:
        response_data['message'] = message
    if data is not None:
        response_data['data'] = data
    response_data.update(extra)
    
    return Response(response_data, status=status_code)
