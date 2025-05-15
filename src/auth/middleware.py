import uuid
from auth.logging_config import logger

class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = str(uuid.uuid4())
        request.request_id = request_id

        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')

        logger.info(
            'Request started',
            extra={
                'request_id': request_id,
                'method': request.method,
                'path': request.path,
                'ip': ip,
                'user_id': request.user.id if request.user.is_authenticated else None
            }
        )

        response = self.get_response(request)

        logger.info(
            'Request finished',
            extra={
                'request_id': request_id,
                'status_code': response.status_code,
                'ip': ip,
                'user_id': request.user.id if request.user.is_authenticated else None
            }
        )

        return response

    def process_exception(self, request, exception):
        logger.error(
            'Request failed',
            extra={
                'request_id': getattr(request, 'request_id', None),
                'error': str(exception),
                'user_id': request.user.id if request.user.is_authenticated else None
            },
            exc_info=True
        )
        return None