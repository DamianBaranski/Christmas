"""Organiser panel at /admin/ (staff only)."""
import secrets

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.utils.translation import gettext as _, ngettext

from .models import User, UserActivationSteps, SiteSettings, DrawRun, Exclusion, WishlistFile, FileActivationSteps
from .forms import EventSettingsForm
from .mail import acount_activated_mail, user_registration_mail, letter_reminder_mail
from . import draw


def _users(step):
    return User.objects.filter(activation_step=step).order_by('name', 'surname')


def _without_letter():
    """Ready participants who haven't confirmed a letter to Santa yet."""
    with_letter = set(m.lower() for m in WishlistFile.objects
                      .exclude(activation_step=FileActivationSteps.EMAIL).values_list('mail', flat=True))
    return [u for u in _users(UserActivationSteps.READY) if u.mail.lower() not in with_letter]


@staff_member_required
def panel(request, event_form=None):
    site = SiteSettings.load()
    last_run = DrawRun.objects.order_by('-created_at').first()
    pairs = list(last_run.pairs.select_related('giver', 'receiver')) if last_run else []
    ready = list(_users(UserActivationSteps.READY))
    context = {
        'site_settings': site,
        'event_form': event_form or EventSettingsForm(instance=site),
        'theme_choices': SiteSettings.THEME_CHOICES,
        'ready': ready,
        'waiting_admin': _users(UserActivationSteps.ADMIN),
        'waiting_email': _users(UserActivationSteps.EMAIL),
        'without_letter': _without_letter(),
        'exclusions': Exclusion.objects.select_related('giver', 'receiver').order_by('giver__name', 'giver__surname'),
        'all_users': User.objects.order_by('name', 'surname'),
        'draw_possible': draw.draw_possible(ready, draw.load_locks()),
        'last_run': last_run,
        'pairs': pairs,
        'sent_count': sum(p.sent for p in pairs),
        'failed': [p for p in pairs if not p.sent],
    }
    return render(request, 'website/panel.html', context)


@staff_member_required
@require_POST
def save_event(request):
    form = EventSettingsForm(request.POST, instance=SiteSettings.load())
    if not form.is_valid():
        messages.error(request, _('Popraw zaznaczone pola.'))
        return panel(request, event_form=form)
    form.save()
    messages.success(request, _('Zapisano ustawienia wydarzenia.'))
    return redirect('panel')


def _send_each(users, send):
    sent = failed = 0
    for u in users:
        try:
            send(u)
            sent += 1
        except Exception:
            failed += 1
    return sent, failed


def _report(request, sent, failed):
    if sent:
        messages.success(request, ngettext('Wysłano %(n)d przypomnienie.', 'Wysłano %(n)d przypomnień.', sent) % {'n': sent})
    if failed:
        messages.warning(request, ngettext('Nie udało się wysłać %(n)d maila.', 'Nie udało się wysłać %(n)d maili.', failed) % {'n': failed})
    if not sent and not failed:
        messages.info(request, _('Nie ma do kogo wysłać przypomnienia.'))


@staff_member_required
@require_POST
def remind_confirm(request):
    users = _users(UserActivationSteps.EMAIL)
    _report(request, *_send_each(users, lambda u: user_registration_mail(u.mail, u.activation_token, u.language)))
    return redirect('panel')


@staff_member_required
@require_POST
def remind_letter(request):
    _report(request, *_send_each(_without_letter(), letter_reminder_mail))
    return redirect('panel')


@staff_member_required
@require_POST
def set_theme(request):
    value = request.POST.get('theme')
    if value in dict(SiteSettings.THEME_CHOICES):
        s = SiteSettings.load()
        s.theme = value
        s.save()
        messages.success(request, _('Zapisano styl strony: {}.').format(s.get_theme_display()))
    return redirect('panel')


@staff_member_required
@require_POST
def approve_user(request, pk):
    user = get_object_or_404(User, pk=pk, activation_step=UserActivationSteps.ADMIN)
    user.activation_step = UserActivationSteps.READY
    user.activation_token = secrets.token_hex(16)
    user.save()
    try:
        acount_activated_mail(user.mail, user.language)
        messages.success(request, _('Zaakceptowano {} {}.').format(user.name, user.surname))
    except Exception as e:
        messages.warning(request, _('Zaakceptowano {} {}, ale nie udało się wysłać maila: {}').format(user.name, user.surname, e))
    return redirect('panel')


@staff_member_required
@require_POST
def run_draw(request):
    if request.POST.get('confirm') != 'yes':
        messages.error(request, _('Zaznacz potwierdzenie, aby uruchomić losowanie.'))
        return redirect('panel')
    try:
        run = draw.run_draw()
    except draw.DrawError as e:
        messages.error(request, str(e))
        return redirect('panel')
    total = run.pairs.count()
    sent = run.pairs.filter(sent=True).count()
    if sent == total:
        messages.success(request, ngettext('Losowanie zakończone! Wysłano %(n)d mail.', 'Losowanie zakończone! Wysłano %(n)d maili.', total) % {'n': total})
    else:
        messages.warning(request, _('Losowanie zakończone, ale wysłano tylko {} z {} maili. Możesz ponowić wysyłkę.').format(sent, total))
    return redirect('panel')


@staff_member_required
@require_POST
def resend_failed(request):
    run = DrawRun.objects.order_by('-created_at').first()
    if run:
        failed = draw.send_pairs(run.pairs.select_related('giver', 'receiver').filter(sent=False))
        if failed:
            messages.warning(request, ngettext('Nadal nie udało się wysłać %(n)d maila.', 'Nadal nie udało się wysłać %(n)d maili.', failed) % {'n': failed})
        else:
            messages.success(request, _('Wszystkie maile zostały wysłane.'))
    return redirect('panel')


@staff_member_required
@require_POST
def add_exclusion(request):
    giver = User.objects.filter(pk=request.POST.get('giver')).first()
    receiver = User.objects.filter(pk=request.POST.get('receiver')).first()
    if not giver or not receiver:
        messages.error(request, _('Wybierz obie osoby.'))
        return redirect('panel')
    if giver.pk == receiver.pk:
        messages.error(request, _('Wybierz dwie różne osoby.'))
        return redirect('panel')

    directions = [(giver, receiver)]
    if request.POST.get('both') == 'yes':
        directions.append((receiver, giver))
    created = sum(Exclusion.objects.get_or_create(giver=g, receiver=r)[1] for g, r in directions)

    if created:
        g = '{} {}'.format(giver.name, giver.surname)
        r = '{} {}'.format(receiver.name, receiver.surname)
        if len(directions) == 2:
            messages.success(request, _('Dodano blokadę w obie strony: {} ↔ {}.').format(g, r))
        else:
            messages.success(request, _('Dodano blokadę: {} nie losuje {}.').format(g, r))
    else:
        messages.info(request, _('Taka blokada już istnieje.'))
    return redirect('/admin/#blokady')


@staff_member_required
@require_POST
def delete_exclusion(request, pk):
    Exclusion.objects.filter(pk=pk).delete()
    messages.success(request, _('Usunięto blokadę.'))
    return redirect('/admin/#blokady')
