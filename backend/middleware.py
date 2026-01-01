"""
Custom middleware for API request/response logging
"""
import time
import logging

logger = logging.getLogger('api')

class APILoggingMiddleware:
    """
    Logs all API requests and responses
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Start timer
        start_time = time.time()
        
        # Get request info
        method = request.method
        path = request.path
        user = getattr(request, 'user', None)
        username = user.username if user and user.is_authenticated else 'anonymous'
        
        # Log request
        logger.info(
            f"API Request: {method} {path} | User: {username} | IP: {self.get_client_ip(request)}"
        )
        
        # Process request
        response = self.get_response(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log response
        status_code = response.status_code
        logger.info(
            f"API Response: {method} {path} | Status: {status_code} | "
            f"Duration: {duration:.3f}s | User: {username}"
        )
        
        return response
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

