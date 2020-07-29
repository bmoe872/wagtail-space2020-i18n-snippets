# Home App
from django.conf import settings
from django.core.exceptions import ValidationError, PermissionDenied
from django.forms.utils import ErrorList

from wagtail.core import hooks
from wagtail.core.blocks.field_block import PageChooserBlock
from wagtail.core.fields import StreamField
from wagtail.core.models import Page

from .models import HomePage


@hooks.register('before_copy_page')
def before_copy_page(request, page):
    """
    Home Pages need to have their slug as a specified value based on the region they are in.
    The HomePage model has a custom `clean` method that automatically populates the slug based
    on the region selected. We want this since we don't expect the client to know what all the
    region slugs are. Therefore if the HomePage gets copied, we want to ensure that the region
    has not been selected before, because we can't have 2 of the same slug value. So before the
    page gets copied we do a soft reassignment to the first available region that has not yet been
    specified, and then copy that page. The soft reassignment means that the original page doesn't
    get the new region value, but the copied page will. If wagtail opened up the copy page fields
    a bit more, this would be much easier to do. Also we use the set subtraction, because it's much
    faster.
    """
    if page.specific_class == HomePage:
        current_regions = [region.region for region in page.get_siblings().specific()]
        all_regions = [region[0] for region in getattr(settings, "REGIONS")]

        available_regions = set(all_regions) - set(current_regions)

        if len(available_regions) > 0:
            page.specific.region = available_regions.pop()
        else:
            raise PermissionDenied("No more Regions available")


@hooks.register('after_copy_page')
def after_copy_page(self, request, page):
    if page.specific_class == HomePage:
        # First go through all the fields on the HomePage to find the stream fields
        home_page = page.specific
        for field in home_page._meta.get_fields():
            if isinstance(field, StreamField):
                # These are all fields that are StreamFields
                # Now need to run through each streamfield, and see if its a PageChooserBlock OR
                # If its a struct block that contains a PageChooserBlock
                for block in field.value_from_object(home_page):
                    if isinstance(block.block, PageChooserBlock):
                        if block.value.specific.get_region() != home_page.slug:
                            other_pages = Page.objects.filter(slug=block.value.slug)
                            for page in other_pages:
                                if page.specific.get_region() == home_page.slug:
                                    block.value = page

        home_page.save()