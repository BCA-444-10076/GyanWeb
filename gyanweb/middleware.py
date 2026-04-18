from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
import re

class DisableCSRFForAPI(MiddlewareMixin):
    def process_request(self, request):
        if request.path_info.startswith('/api/') or any(re.match(pattern, request.path_info) for pattern in getattr(settings, 'CSRF_EXEMPT_URLS', [])):
            setattr(request, '_dont_enforce_csrf_checks', True)
