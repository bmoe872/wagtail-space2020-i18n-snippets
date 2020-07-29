from django.core.exceptions import ValidationError
from django.forms.utils import ErrorList
from django.utils.translation import ugettext_lazy as _

from wagtail.core import blocks
from wagtail.images.blocks import ImageChooserBlock


class ImageBlock(blocks.StructBlock):
    image = ImageChooserBlock()
    image_alt_text = blocks.CharBlock(help_text=_("Explain the image"))
    image_caption = blocks.TextBlock(required=False)

    class Meta:
        icon = 'fa-image'

    def clean(self, value):
        results = super(ImageBlock, self).clean(value)
        errors = {}

        if value['image'] and not value['image_alt_text']:
            errors['image_alt_text'] = ErrorList([
                _('Must have image alt text with an image'),
            ])

        if errors:
            raise ValidationError(_('Validation errors in Image Block'), params=errors)

        return results