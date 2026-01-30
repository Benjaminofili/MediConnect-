from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    """
    Custom exception handler for consistent error responses.
    """
    response = exception_handler(exc, context)
    
    if response is not None:
        custom_response = {
            'success': False,
            'error': {
                'status_code': response.status_code,
                'message': get_error_message(response),
                'details': response.data if isinstance(response.data, dict) else {'error': response.data}
            }
        }
        response.data = custom_response
    
    return response


def get_error_message(response):
    """Get a human-readable error message."""
    status_code = response.status_code
    
    messages = {
        400: 'Bad Request',
        401: 'Authentication Required',
        403: 'Permission Denied',
        404: 'Not Found',
        405: 'Method Not Allowed',
        500: 'Internal Server Error',
    }
    
    return messages.get(status_code, 'An error occurred')