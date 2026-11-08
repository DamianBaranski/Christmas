from django.utils.translation import get_language, gettext as _

from .models import SiteSettings


def site(request):
    """Site settings for every template. '?theme=day' previews a theme without saving it."""
    try:
        s = SiteSettings.load()
    except Exception:  # e.g. migrations not applied yet
        s = SiteSettings()
    preview = request.GET.get('theme')
    return {
        'site': s,
        'theme': preview if preview in dict(SiteSettings.THEME_CHOICES) else s.theme,
        'party_host': s.party_host,
        'custom_intro': s.intro_for(get_language()),
        # site name in the tab, header logo and page titles
        'site_title': _('List do Mikołaja') if s.letters_enabled else _('Zostań Mikołajem'),
    }
