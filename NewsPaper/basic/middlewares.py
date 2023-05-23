import pytz

from django.utils import timezone
from pytz_deprecation_shim import UnknownTimeZoneError


class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            tzname = request.session.get('django_timezone')
        except UnknownTimeZoneError:
            tzname = 'UTC'
        #tzname = request.session.get('django_timezone')  # пытаемся забрать часовой пояс из сессии
        #  если он есть в сессии, то выставляем такой часовой пояс. Если же его нет, значит он не установлен, и часовой пояс надо выставить по умолчанию (на время сервера)
        if tzname:
            timezone.activate(pytz.timezone(tzname))
        else:
            timezone.deactivate()
        return self.get_response(request)
