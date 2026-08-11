import markdown as md
from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(name='markdownify')
def markdownify(value):
    """
    Converts a markdown string into HTML.
    """
    if not value:
        return ""

    # Escape first so literal HTML in the source (e.g. <script>) can't survive
    # markdown's raw-HTML passthrough and execute in the browser.
    html = md.markdown(escape(value), extensions=['extra', 'sane_lists'])
    return mark_safe(html)
