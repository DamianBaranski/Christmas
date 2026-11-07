# -*- coding: utf-8 -*-
# Emails go through Django's email backend, configured in .env (see .env.example).
from django.core.mail import EmailMessage
from django.utils import translation
from django.utils.translation import gettext as _

from django.conf import settings


def send_mail(address, topic, message, attachments=()):
    """Send one plain-text email. attachments: iterable of (filename, content, mimetype)."""
    email = EmailMessage(topic, message, settings.DEFAULT_FROM_EMAIL, [address])
    for attachment in attachments:
        email.attach(*attachment)
    email.send(fail_silently=False)


def site_url():
    from .models import SiteSettings
    return SiteSettings.load().site_url.rstrip('/')


def user_registration_mail(user_mail, token, lang=settings.LANGUAGE_CODE):
    with translation.override(lang):
        topic = _("Rejestracja na losowanie wigilijne")
        message = _("Aby potwierdzić rejestrację na losowanie wigilijne, kliknij link:\n\n{url}\n\n"
                    "Po kliknięciu w link poczekaj na potwierdzenie od organizatora.").format(
            url=site_url() + "/confirm_user/email/" + token + "/")
    send_mail(user_mail, topic, message)


def admin_registration_mail(admin_mail, user_mail, user_name, token, lang=settings.LANGUAGE_CODE):
    with translation.override(lang):
        topic = _("Rejestracja na losowanie wigilijne")
        message = _("Czy potwierdzasz {mail} {name}? {url}").format(
            mail=user_mail, name=user_name, url=site_url() + "/confirm_user/admin/" + token + "/")
    send_mail(admin_mail, topic, message)


def acount_activated_mail(user_mail, lang=settings.LANGUAGE_CODE):
    with translation.override(lang):
        topic = _("Rejestracja na losowanie wigilijne")
        message = _("Twoje konto jest już aktywne.")
    send_mail(user_mail, topic, message)


def wishlist_mail(user_mail, token, lang=settings.LANGUAGE_CODE):
    with translation.override(lang):
        topic = _("List do Świętego Mikołaja")
        message = _("Czy potwierdzasz przesłanie listu do Świętego Mikołaja?\n\nJeśli tak, kliknij link:\n{url}").format(
            url=site_url() + "/confirm_wishlist/" + token + "/")
    send_mail(user_mail, topic, message)


def letter_reminder_mail(user):
    with translation.override(user.language or settings.LANGUAGE_CODE):
        topic = _("List do Świętego Mikołaja")
        message = _("Cześć {name},\n\n"
                    "nie dostaliśmy jeszcze Twojego listu do Mikołaja. Nie jest obowiązkowy, "
                    "ale bardzo pomoże osobie, która Cię wylosuje, w wyborze prezentu.\n\n"
                    "Możesz go wysłać tutaj: {url}\n\n"
                    "Pozdrawiam\nŚwięty Mikołaj").format(name=user.name, url=site_url() + "/wishlist/")
    send_mail(user.mail, topic, message)


def event_summary(site):
    """Human-readable event details for emails (in the active language), or ''."""
    from django.utils import formats, timezone
    lines = []
    if site.event_at:
        when = formats.date_format(timezone.localtime(site.event_at), 'l, j E Y, H:i')
        lines.append(_("Kiedy: {when}").format(when=when))
    if site.event_address:
        lines.append(_("Gdzie: {where}").format(where=site.event_address))
    if site.event_details:
        lines.append(site.event_details)
    return "\n".join(lines)


def _ics_escape(text):
    return (text.replace('\\', '\\\\').replace(';', '\\;').replace(',', '\\,')
            .replace('\r\n', '\\n').replace('\n', '\\n'))


def event_ics(site):
    """A calendar invite (.ics) for the Christmas Eve party, or None without a date."""
    import datetime
    import uuid
    from datetime import timezone as dt_tz
    if not site.event_at:
        return None
    fmt = '%Y%m%dT%H%M%SZ'
    start = site.event_at.astimezone(dt_tz.utc)
    end = start + datetime.timedelta(hours=4)
    summary = _("Wigilia u {host}").format(host=site.party_host)
    lines = [
        'BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//List do Mikolaja//PL', 'METHOD:PUBLISH',
        'BEGIN:VEVENT',
        'UID:{}@list-do-mikolaja'.format(uuid.uuid5(uuid.NAMESPACE_URL, site.site_url + str(start))),
        'DTSTAMP:' + datetime.datetime.now(dt_tz.utc).strftime(fmt),
        'DTSTART:' + start.strftime(fmt),
        'DTEND:' + end.strftime(fmt),
        'SUMMARY:' + _ics_escape(summary),
    ]
    if site.event_address:
        lines.append('LOCATION:' + _ics_escape(site.event_address))
    if site.event_details:
        lines.append('DESCRIPTION:' + _ics_escape(site.event_details))
    lines += ['END:VEVENT', 'END:VCALENDAR']
    return '\r\n'.join(lines) + '\r\n'
