from django.conf import settings
from django.contrib.gis.geoip2 import GeoIP2
from django.db import models
from django.http import HttpResponseRedirect
from django.utils import translation
from django.utils.translation import ugettext_lazy as _

from wagtail.admin.edit_handlers import FieldPanel
from wagtail.core.models import Page

from ipware import get_client_ip

from apps.home.models import HomePage


class LanguageRedirectionPage(Page):
    parent_page_types = ['wagtailcore.page']

    # This will only return a language that is in the LANGUAGES Django setting
    def serve(self, request):
        language = translation.get_language_from_request(request)

        if request.session.get('site_language'):
            language = request.session.get('site_language')

        translation.activate(language)

        return HttpResponseRedirect(self.url + language + '/')


class RegionRedirectionPage(Page):
    parent_page_types = ['LanguageRedirectionPage']

    language = models.CharField(
        max_length=5,
        choices=getattr(settings, "LANGUAGES"),
        help_text=_("Indicates the language this page serves as the main home page."),
        unique=True
    )

    content_panels = Page.content_panels + [
        FieldPanel('language')
    ]

    def children(self):
        return self.get_children().specific().live()

    def serve(self, request):
        default = super(RegionRedirectionPage, self).serve(request)

        # Check if user came here from a different page
        if 'QUERY_STRING' in request.META and 'selector=true' in request.META['QUERY_STRING']:
            # Then they came from a page looking to go to a different page.
            # Which also means we can assume they don't want to be prompted
            # to change language or region. This will get used by the includes
            # prompt (language_location_prompt.html), so we set a cookie to
            # make sure they don't get prompted again
            request.session['chosen_region_or_language'] = True
            # We also want to make sure that we store the correct site_region cookie
            # on the home page, so we redirect them to the correct region home page,
            # See how we handle that in get_context.
            return default

        elif request.session.get('site_region'):
            # We know that they have been to the home page once before, and
            # they're not looking to change region/language otherwise the above
            # case would have caught them.
            return HttpResponseRedirect(self.url + request.session.get('site_region') + '/')

        # Check Users IP
        client_ip, is_routable = get_client_ip(request)

        if client_ip:
            if is_routable:
                geo = GeoIP2()
                detected_region = geo.country(client_ip)['country_code']

                if not HomePage.objects.filter(region=detected_region.lower()):
                    # Detected region does not have a home page, so bring them to self for them to pick
                    return default
                # This means that the region detected is an available HomePage, direct user there, automatically.
                return HttpResponseRedirect(self.url + detected_region.lower() + '/')

        return default

    def clean(self):
        super().clean()
        if self.slug != self.language:
            self.slug = self.language

    def get_context(self, request):
        context = super(RegionRedirectionPage, self).get_context(request)

        client_ip, is_routable = get_client_ip(request)

        if client_ip is None:
            # Default to US, this means we couldn't get the client's IP address
            detected_region = 'US'
        else:
            # We got the client's IP address
            if is_routable:
                # The client's IP address is publicly routable on the Internet
                geo = GeoIP2()
                detected_region = geo.country(client_ip)['country_code']
            else:
                # The client's IP address is private
                detected_region = 'private'

        context['detected_region'] = detected_region
        context['detected_ip'] = client_ip
        context['detected_language'] = translation.get_language_from_request(request)

        if 'selector=true' in request.META['QUERY_STRING']:
            # We want to make sure all the links provided on this page
            # have a querystring parameter to notify the homepage
            # to store a new cookie on where they want to go in the future.
            context['selecting_new_region_or_language'] = True

        return context

