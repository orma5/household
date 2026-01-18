import markdown as md
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(name='markdownify')
def markdownify(value):
    """
    Converts a markdown string into HTML.
    """
    if not value:
        return ""
    
    # We can add extensions here later if needed (e.g., 'extra', 'toc')
    html = md.markdown(value, extensions=['extra', 'sane_lists'])
    return mark_safe(html)
