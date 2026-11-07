from django.conf import settings
from django.utils import translation


class LanguageMiddleware:
    """Use the language the visitor picked (cookie set by the header switch).

    Unlike Django's LocaleMiddleware this ignores the browser's Accept-Language,
    so everyone sees Polish until they explicitly switch.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.available = dict(settings.LANGUAGES)

    def __call__(self, request):
        lang = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME)
        if lang not in self.available:
            lang = settings.LANGUAGE_CODE
        translation.activate(lang)
        request.LANGUAGE_CODE = lang
        response = self.get_response(request)
        response.headers.setdefault('Content-Language', lang)
        return response
