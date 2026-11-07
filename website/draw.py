"""Secret Santa draw: pick a single gift-giving cycle that respects exclusions."""
from random import shuffle

from django.utils import translation
from django.utils.translation import gettext as _

from .models import User, UserActivationSteps, DrawRun, DrawPair, Exclusion, SiteSettings
from . import mail

MAX_ATTEMPTS = 20000


class DrawError(Exception):
    pass


def load_locks():
    """Exclusions as [(giver_mail, receiver_mail), ...]: giver must not draw receiver."""
    return [(e.giver.mail.lower(), e.receiver.mail.lower())
            for e in Exclusion.objects.select_related('giver', 'receiver')]


def ready_users():
    return list(User.objects.filter(activation_step=UserActivationSteps.READY))


def compute_pairs(users, locks, attempts=MAX_ATTEMPTS):
    """Return [(giver, receiver), ...] forming one cycle, or raise DrawError."""
    if len(users) < 2:
        raise DrawError(_('Do losowania potrzeba co najmniej 2 potwierdzonych osób.'))
    blocked = set(locks)
    users = list(users)
    for _attempt in range(attempts):
        shuffle(users)
        pairs = [(users[i], users[(i + 1) % len(users)]) for i in range(len(users))]
        if not any((g.mail.lower(), r.mail.lower()) in blocked for g, r in pairs):
            return pairs
    raise DrawError(_('Nie udało się znaleźć losowania spełniającego wszystkie blokady. Usuń część blokad w panelu.'))


def send_draw_mail(giver, receiver):
    site = SiteSettings.load()
    with translation.override(giver.language or 'pl'):
        subject = _('Wyniki losowania')
        message = _(
            "{giver},\n\n"
            "Święty Mikołaj nie da rady samemu obdarować wszystkich, musisz mu pomóc.\n"
            "Zrób prezent dla: {receiver} (budżet: {budget}).\n"
            "Pod tym adresem sprawdzisz, czy wylosowana osoba przesłała list: {check_url}\n"
            "Jeśli jeszcze nie przesłałeś(-aś) swojego listu, możesz to zrobić tutaj: {wishlist_url}\n"
        ).format(
            giver=giver.name,
            receiver=receiver.name + ' ' + receiver.surname,
            budget=site.gift_budget,
            check_url=mail.site_url() + '/checkwishlist/' + receiver.activation_token + '/',
            wishlist_url=mail.site_url() + '/wishlist/',
        )
        event = mail.event_summary(site)
        if event:
            message += "\n" + _("Do zobaczenia na wigilii!") + "\n" + event + "\n"
        message += "\n" + _("Pozdrawiam\nŚwięty Mikołaj") + "\n"
        ics = mail.event_ics(site)
    attachments = [('wigilia.ics', ics, 'text/calendar')] if ics else []
    mail.send_mail(giver.mail, subject, message, attachments)


def send_pairs(pairs):
    """Send mails for DrawPair objects that were not sent yet. Returns number of failures."""
    failed = 0
    for pair in pairs:
        if pair.sent:
            continue
        try:
            send_draw_mail(pair.giver, pair.receiver)
            pair.sent, pair.error = True, ''
        except Exception as e:  # keep going, the organiser can resend later
            pair.error = str(e) or e.__class__.__name__
            failed += 1
        pair.save()
    return failed


def draw_possible(users, locks):
    """Quick feasibility check for the panel (None when there are too few people)."""
    if len(users) < 2:
        return None
    try:
        compute_pairs(users, locks, attempts=3000)
        return True
    except DrawError:
        return False


def run_draw():
    pairs = compute_pairs(ready_users(), load_locks())
    run = DrawRun.objects.create()
    objs = [DrawPair.objects.create(run=run, giver=g, receiver=r) for g, r in pairs]
    send_pairs(objs)
    return run
