from django.contrib.gis.geoip2 import GeoIP2
from django.utils import translation

from ipware import get_client_ip


class LocationPromptMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if we've already detected their region.
        if not hasattr(request, "middleware_detected_region"):
            # Get client's IP
            client_ip, is_routable = get_client_ip(request)
            middleware_detected_region = None
            if client_ip:
                if is_routable:
                    geo = GeoIP2()
                    middleware_detected_region = geo.country(client_ip)['country_code'].lower()

            request.middleware_detected_language = translation.get_language_from_request(request)

            if middleware_detected_region:
                request.middleware_detected_region = middleware_detected_region
            else:
                # Default to us for region
                request.middleware_detected_region = 'us'

        response = self.get_response(request)

        return response

