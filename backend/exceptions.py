import logging
import traceback
from rest_framework.views import exception_handler
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated
from rest_framework import status
from rest_framework.response import Response

error_logger = logging.getLogger('errors')

def custom_exception_handler(exc, context):
    """
    Custom exception handler to return user-friendly error messages
    Also logs errors with full stack traces
    """
    response = exception_handler(exc, context)
    
    # Get request info for logging
    request = context.get('request')
    user = getattr(request, 'user', None) if request else None
    username = user.username if user and user.is_authenticated else 'anonymous'
    path = request.path if request else 'unknown'
    method = request.method if request else 'unknown'
    
    # Log the error with full stack trace
    error_logger.error(
        f"Error in {method} {path} | User: {username} | "
        f"Exception: {type(exc).__name__}: {str(exc)}",
        exc_info=True,
        extra={
            'path': path,
            'method': method,
            'user': username,
            'exception_type': type(exc).__name__,
        }
    )

    if isinstance(exc, (AuthenticationFailed, NotAuthenticated)):
        return Response(
            {
                'error': 'Authentication required. Please login.',
                'message': 'Invalid or missing token. Please login to get a valid token.'
            },
            status=status.HTTP_401_UNAUTHORIZED
        )

    return response

