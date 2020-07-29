from django.db import models

from wagtail.admin.edit_handlers import PageChooserPanel, MultiFieldPanel
from wagtail.core.models import Page


class TranslatablePageMixin:
    def get_language(self):
        """
        This returns the language code for this page.
        """
        # Look through ancestors of this page for its language homepage
        # The language homepage is located at depth 3
        language_homepage = self.get_ancestors(inclusive=True).get(depth=3)

        # The slug of language homepages should always be set to the language code
        return language_homepage.slug

    def get_admin_display_title(self):
        result = super().get_admin_display_title()

        try:
            language = self.get_language()
        except Page.DoesNotExist:
            return result

        if language:
            return f"{result} - {language.upper()}"

        return result


class RegionalizablePageMixin:
    def get_region(self):
        """
        This returns the region code for this page.
        """
        # Look through ancestors of this page for its language region homepage.
        # The region homepage is located at depth 4
        region_homepage = self.get_ancestors(inclusive=True).get(depth=4)

        # The slug of this page should always be set to the region.
        return region_homepage.slug

    def get_admin_display_title(self):
        result = super().get_admin_display_title()

        try:
            region = self.get_region()
        except Page.DoesNotExist:
            return result

        if region:
            return f"{result} - {region.upper()}"

        return result

    def get_alternate_pages(self):
        alternate_pages = Page.objects.filter(slug=self.slug)

        return alternate_pages



