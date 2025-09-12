import logging
from rest_framework.throttling import SimpleRateThrottle

logger = logging.getLogger(__name__)

class BurstThrottle(SimpleRateThrottle):
    """
    Custom burst throttle that allows 10 requests per second.
    """
    scope = 'burst'
    rate = '10/second'

    def allow_request(self, request, view):
        allowed = super().allow_request(request, view)
        if not allowed:
            logger.warning(
                f"Burst throttle exceeded for {request.method} {request.path} from {self.get_ident(request)}"
            )
        return allowed

class WhitelistThrottle(SimpleRateThrottle):
    """
    Throttle that bypasses throttling for whitelisted IPs or API keys.
    """
    scope = 'whitelist'

    def allow_request(self, request, view):
        # Define whitelisted IPs or API keys
        whitelisted_ips = ['127.0.0.1', 'localhost', '192.168.1.4']  # Add your internal IPs
        whitelisted_api_keys = ['your-internal-api-key']  # Add API keys if using

        client_ip = self.get_ident(request)
        api_key = request.META.get('HTTP_X_API_KEY')  # Assuming API key in header

        if client_ip in whitelisted_ips or api_key in whitelisted_api_keys:
            return True  # Bypass throttling

        # If not whitelisted, apply no rate limit (or you can set a high rate)
        # For now, allow unlimited for non-whitelisted, but you can adjust
        return True  # Change to False or set rate if needed

    def get_rate(self):
        # No rate limit for whitelisted, but if you want to apply a rate, return a string like '1000/hour'
        return None
