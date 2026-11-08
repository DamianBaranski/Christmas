from unittest import mock

from django.contrib.auth.models import User as AuthUser
from django.test import TestCase

from .draw import compute_pairs, DrawError
from .models import User, UserActivationSteps, SiteSettings, DrawRun


def make_user(i, step=UserActivationSteps.READY):
    return User.objects.create(name='N%d' % i, surname='S%d' % i, mail='u%d@x.pl' % i,
                               activation_token='t%d' % i, activation_step=step)


class ComputePairsTests(TestCase):
    def test_single_cycle(self):
        users = [make_user(i) for i in range(6)]
        pairs = compute_pairs(users, [])
        self.assertEqual(sorted(g.pk for g, _ in pairs), sorted(u.pk for u in users))
        self.assertEqual(sorted(r.pk for _, r in pairs), sorted(u.pk for u in users))
        self.assertTrue(all(g != r for g, r in pairs))

    def test_respects_locks(self):
        users = [make_user(i) for i in range(4)]
        locks = [('u0@x.pl', 'u1@x.pl'), ('u1@x.pl', 'u0@x.pl')]
        for _ in range(30):
            for g, r in compute_pairs(users, locks):
                self.assertNotIn((g.mail, r.mail), locks)

    def test_impossible(self):
        users = [make_user(i) for i in range(2)]
        with self.assertRaises(DrawError):
            compute_pairs(users, [('u0@x.pl', 'u1@x.pl')])

    def test_too_few(self):
        with self.assertRaises(DrawError):
            compute_pairs([make_user(0)], [])


@mock.patch('website.draw.load_locks', return_value=[])
@mock.patch('website.mail.send_mail')
class PanelTests(TestCase):
    def setUp(self):
        AuthUser.objects.create_user('boss', password='pw', is_staff=True)

    def login(self):
        self.client.login(username='boss', password='pw')

    def test_requires_staff(self, send, locks):
        r = self.client.get('/admin/')
        self.assertEqual(r.status_code, 302)
        self.assertIn('/admin/db/login/', r['Location'])

    def test_panel_renders(self, send, locks):
        self.login()
        make_user(1)
        r = self.client.get('/admin/')
        self.assertContains(r, 'Panel organizatora')

    def test_set_theme(self, send, locks):
        self.login()
        self.client.post('/admin/theme/', {'theme': 'cozy'})
        self.assertEqual(SiteSettings.load().theme, 'cozy')
        self.assertContains(self.client.get('/'), 'data-theme="cozy"')
        self.client.post('/admin/theme/', {'theme': 'bogus'})
        self.assertEqual(SiteSettings.load().theme, 'cozy')

    def test_theme_preview_param(self, send, locks):
        self.assertContains(self.client.get('/?theme=cozy'), 'data-theme="cozy"')
        self.assertContains(self.client.get('/'), 'data-theme="winter"')

    def test_approve(self, send, locks):
        self.login()
        u = make_user(1, UserActivationSteps.ADMIN)
        self.client.post('/admin/approve/%d/' % u.pk)
        u.refresh_from_db()
        self.assertEqual(u.activation_step, str(UserActivationSteps.READY))
        send.assert_called_once()

    def test_draw_requires_confirmation(self, send, locks):
        self.login()
        for i in range(3):
            make_user(i)
        self.client.post('/admin/draw/', {})
        self.assertEqual(DrawRun.objects.count(), 0)
        send.assert_not_called()

    def test_draw_and_resend(self, send, locks):
        self.login()
        for i in range(4):
            make_user(i)
        send.side_effect = [None, Exception('smtp down'), None, None]
        self.client.post('/admin/draw/', {'confirm': 'yes'})
        run = DrawRun.objects.get()
        self.assertEqual(run.pairs.count(), 4)
        self.assertEqual(run.pairs.filter(sent=False).count(), 1)

        send.side_effect = None
        self.client.post('/admin/resend/')
        self.assertEqual(run.pairs.filter(sent=False).count(), 0)
        self.assertEqual(send.call_count, 5)


class ExclusionTests(TestCase):
    def setUp(self):
        AuthUser.objects.create_user('boss', password='pw', is_staff=True)
        self.client.login(username='boss', password='pw')
        self.a, self.b, self.c = make_user(0), make_user(1), make_user(2)

    def test_add_both_directions_and_duplicates(self):
        from .models import Exclusion
        self.client.post('/admin/exclusions/add/', {'giver': self.a.pk, 'receiver': self.b.pk, 'both': 'yes'})
        self.assertEqual(Exclusion.objects.count(), 2)
        self.client.post('/admin/exclusions/add/', {'giver': self.a.pk, 'receiver': self.b.pk, 'both': 'yes'})
        self.assertEqual(Exclusion.objects.count(), 2)
        self.client.post('/admin/exclusions/add/', {'giver': self.a.pk, 'receiver': self.c.pk})
        self.assertEqual(Exclusion.objects.count(), 3)

    def test_rejects_same_person(self):
        from .models import Exclusion
        self.client.post('/admin/exclusions/add/', {'giver': self.a.pk, 'receiver': self.a.pk})
        self.assertEqual(Exclusion.objects.count(), 0)

    def test_delete(self):
        from .models import Exclusion
        e = Exclusion.objects.create(giver=self.a, receiver=self.b)
        self.client.post('/admin/exclusions/%d/delete/' % e.pk)
        self.assertEqual(Exclusion.objects.count(), 0)

    def test_draw_uses_db_exclusions(self):
        from .models import Exclusion
        from .draw import load_locks
        Exclusion.objects.create(giver=self.a, receiver=self.b)
        for _ in range(20):
            for g, r in compute_pairs([self.a, self.b, self.c], load_locks()):
                self.assertFalse(g == self.a and r == self.b)

    def test_impossible_draw_disables_button(self):
        from .models import Exclusion
        # with 3 people the only cycles are a->b->c->a and a->c->b->a
        Exclusion.objects.create(giver=self.a, receiver=self.b)
        Exclusion.objects.create(giver=self.a, receiver=self.c)
        r = self.client.get('/admin/')
        self.assertContains(r, 'losowanie jest niemożliwe')


@mock.patch('website.mail.send_mail')
class LanguageTests(TestCase):
    def test_polish_by_default_even_for_english_browsers(self, send):
        r = self.client.get('/', HTTP_ACCEPT_LANGUAGE='en-US,en;q=0.9')
        self.assertContains(r, 'Zostań Świętym Mikołajem!')
        self.assertContains(r, '<html lang="pl"')

    def test_switch_to_english(self, send):
        r = self.client.post('/i18n/setlang/', {'language': 'en', 'next': '/wishlist/'})
        self.assertRedirects(r, '/wishlist/', fetch_redirect_response=False)
        r = self.client.get('/')
        self.assertContains(r, 'Become Santa Claus!')
        self.assertContains(r, '<strong>Sign up</strong> using the form below', html=False)
        self.assertContains(r, '<html lang="en"')
        r = self.client.post('/register/', {'name': '', 'surname': 'X', 'mail': 'bad'})
        self.assertContains(r, 'Enter your first name.')

    def test_registration_stores_language_and_emails_in_it(self, send):
        self.client.post('/i18n/setlang/', {'language': 'en', 'next': '/'})
        self.client.post('/register/', {'name': 'John', 'surname': 'Smith', 'mail': 'john@x.pl'})
        self.assertEqual(User.objects.get(mail='john@x.pl').language, 'en')
        _, subject, body = send.call_args[0]
        self.assertEqual(subject, 'Christmas Eve Secret Santa registration')
        self.assertIn('click the link', body)

    def test_draw_mail_in_each_givers_language(self, send):
        from .draw import send_draw_mail
        en, pl = make_user(0), make_user(1)
        en.language = 'en'
        en.save()
        send_draw_mail(en, pl)
        send_draw_mail(pl, en)
        (_, subj_en, body_en), (_, subj_pl, body_pl) = [c[0][:3] for c in send.call_args_list]
        self.assertEqual(subj_en, 'Secret Santa draw results')
        self.assertIn('Please prepare a gift for: N1 S1', body_en)
        self.assertEqual(subj_pl, 'Wyniki losowania')
        self.assertIn('Zrób prezent dla: N0 S0', body_pl)


class EventAndReminderTests(TestCase):
    def setUp(self):
        AuthUser.objects.create_user('boss', password='pw', is_staff=True)
        self.client.login(username='boss', password='pw')

    def test_save_event_settings_and_show_on_home(self):
        r = self.client.post('/admin/event/', {
            'party_host': 'Kasi', 'event_at': '2026-12-24T17:00', 'event_address': 'ul. Śnieżna 1, Kraków',
            'event_details': 'Strój: sweter', 'draw_at': '2026-12-01T20:00', 'gift_budget': '100 zł',
            'site_url': 'https://example.com'})
        self.assertRedirects(r, '/admin/', fetch_redirect_response=False)
        s = SiteSettings.load()
        self.assertEqual(s.party_host, 'Kasi')
        home = self.client.get('/')
        self.assertContains(home, 'wigilię u Kasi')
        self.assertContains(home, 'ul. Śnieżna 1, Kraków')
        self.assertContains(home, '100 zł')
        self.assertContains(home, '24 grudnia 2026')
        self.assertContains(home, 'data-draw-date="2026-12-01T20:00:00+01:00"')

    def test_invalid_event_form_rerenders_panel(self):
        r = self.client.post('/admin/event/', {'party_host': '', 'gift_budget': 'x', 'site_url': 'not a url'})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Popraw zaznaczone pola.')

    def test_no_countdown_without_draw_date(self):
        self.assertNotContains(self.client.get('/'), 'id="zostalo"')

    def test_draw_mail_has_budget_event_and_calendar_invite(self):
        from django.core import mail as outbox
        from django.utils import timezone
        import datetime
        from .draw import send_draw_mail
        s = SiteSettings.load()
        s.gift_budget = '80 zł'
        s.event_at = timezone.make_aware(datetime.datetime(2026, 12, 24, 17, 0))
        s.event_address = 'Kraków, Rynek 1'
        s.save()
        send_draw_mail(make_user(0), make_user(1))
        m = outbox.outbox[0]
        self.assertIn('budżet: 80 zł', m.body)
        self.assertIn('Gdzie: Kraków, Rynek 1', m.body)
        name, content, mimetype = m.attachments[0]
        self.assertEqual((name, mimetype), ('wigilia.ics', 'text/calendar'))
        self.assertIn('DTSTART:20261224T160000Z', content)
        self.assertIn('LOCATION:Kraków\\, Rynek 1', content)

    def test_remind_confirm(self):
        from django.core import mail as outbox
        make_user(0, UserActivationSteps.EMAIL)
        make_user(1)
        self.client.post('/admin/remind/confirm/')
        self.assertEqual([m.to for m in outbox.outbox], [['u0@x.pl']])

    def test_remind_letter_skips_people_with_a_confirmed_letter(self):
        from django.core import mail as outbox
        from .models import WishlistFile, FileActivationSteps
        make_user(0)
        make_user(1)
        make_user(2, UserActivationSteps.EMAIL)
        WishlistFile.objects.create(mail='u0@x.pl', wish_file='a.txt', activation_token='x',
                                    activation_step=FileActivationSteps.READY)
        r = self.client.post('/admin/remind/letter/', follow=True)
        self.assertEqual([m.to for m in outbox.outbox], [['u1@x.pl']])
        self.assertContains(r, 'Wysłano 1 przypomnienie.')


class LetterViewTests(TestCase):
    def test_serves_known_letter_sandboxed(self):
        import os, tempfile
        from django.test import override_settings
        from .models import WishlistFile
        with tempfile.TemporaryDirectory() as d, override_settings(MEDIA_ROOT=d):
            with open(os.path.join(d, 'abc.svg'), 'w') as f:
                f.write('<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>')
            WishlistFile.objects.create(mail='a@x.pl', wish_file='abc.svg', activation_token='t',
                                        activation_step='x')
            r = self.client.get('/letters/abc.svg/')
            self.assertEqual(r.status_code, 200)
            self.assertEqual(r['Content-Security-Policy'], 'sandbox')
            r.close()
            self.assertEqual(self.client.get('/letters/unknown.pdf/').status_code, 404)


class PolishPluralTests(TestCase):
    def test_three_plural_forms(self):
        from django.utils import translation
        from django.utils.translation import ngettext
        with translation.override('pl'):
            f = lambda n: ngettext('Wysłano %(n)d przypomnienie.', 'Wysłano %(n)d przypomnień.', n) % {'n': n}
            self.assertEqual(f(1), 'Wysłano 1 przypomnienie.')
            self.assertEqual(f(3), 'Wysłano 3 przypomnienia.')
            self.assertEqual(f(5), 'Wysłano 5 przypomnień.')
            self.assertEqual(f(22), 'Wysłano 22 przypomnienia.')


class RegistrationLanguageEmailTests(TestCase):
    """Every email goes out in the language chosen when registering, not the current page language."""

    def setUp(self):
        from django.core import mail as outbox
        self.outbox = outbox
        self.en_user = make_user(0)
        self.en_user.language = 'en'
        self.en_user.save()

    def test_letter_confirmation_uses_registration_language(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        import tempfile
        from django.test import override_settings
        with tempfile.TemporaryDirectory() as d, override_settings(MEDIA_ROOT=d):
            # page is in Polish (default), but the person registered in English
            self.client.post('/wishlist/', {'mail': 'u0@x.pl', 'wish_file': SimpleUploadedFile('list.txt', b'hi')})
        self.assertEqual(self.outbox.outbox[0].subject, 'Letter to Santa')
        self.assertIn('Do you confirm sending your letter to Santa?', self.outbox.outbox[0].body)

    def test_activation_and_reminder_use_registration_language(self):
        AuthUser.objects.create_user('boss', password='pw', is_staff=True)
        self.client.login(username='boss', password='pw')
        waiting = make_user(1, UserActivationSteps.ADMIN)
        waiting.language = 'en'
        waiting.save()
        self.client.post('/admin/approve/%d/' % waiting.pk)
        self.client.post('/admin/remind/letter/')
        bodies = [m.body for m in self.outbox.outbox]
        self.assertIn('Your account is now active.', bodies[0])
        self.assertTrue(all("haven't received your letter" in b for b in bodies[1:]))


class IntroTextTests(TestCase):
    def test_default_text_when_empty(self):
        s = SiteSettings.load()
        s.party_host = 'Działu Controllingu'
        s.save()
        r = self.client.get('/')
        self.assertContains(r, 'Zapraszamy na wigilię u Działu Controllingu')
        self.client.post('/i18n/setlang/', {'language': 'en', 'next': '/'})
        self.assertContains(self.client.get('/'), "invited to Christmas Eve at Działu Controllingu")

    def test_custom_text_per_language(self):
        s = SiteSettings.load()
        s.intro_pl = 'Pierwszy akapit.\n\nDrugi <b>akapit</b>.'
        s.intro_en = 'English welcome.'
        s.save()
        r = self.client.get('/')
        self.assertContains(r, '<p>Pierwszy akapit.</p>')
        self.assertContains(r, 'Drugi &lt;b&gt;akapit&lt;/b&gt;.')   # HTML is escaped
        self.assertNotContains(r, 'Zapraszamy na wigilię')
        self.client.post('/i18n/setlang/', {'language': 'en', 'next': '/'})
        r = self.client.get('/')
        self.assertContains(r, '<p>English welcome.</p>')
        self.assertNotContains(r, 'Pierwszy akapit')

    def test_english_falls_back_to_english_default_not_polish_text(self):
        s = SiteSettings.load()
        s.intro_pl = 'Tylko po polsku.'
        s.save()
        self.client.post('/i18n/setlang/', {'language': 'en', 'next': '/'})
        r = self.client.get('/')
        self.assertNotContains(r, 'Tylko po polsku.')
        self.assertContains(r, "invited to Christmas Eve")

    def test_edit_in_panel(self):
        AuthUser.objects.create_user('boss', password='pw', is_staff=True)
        self.client.login(username='boss', password='pw')
        page = self.client.get('/admin/')
        self.assertContains(page, 'name="intro_pl"')
        self.assertContains(page, 'placeholder="Zapraszamy na wigilię u Agnieszki')
        self.client.post('/admin/event/', {'party_host': 'Agnieszki', 'intro_pl': 'Nowy tekst', 'intro_en': 'New text',
                                           'gift_budget': '50 zł', 'site_url': 'https://example.com'})
        s = SiteSettings.load()
        self.assertEqual((s.intro_pl, s.intro_en), ('Nowy tekst', 'New text'))


class LettersToggleTests(TestCase):
    def disable(self):
        s = SiteSettings.load()
        s.letters_enabled = False
        s.save()

    def test_enabled_by_default(self):
        r = self.client.get('/')
        self.assertContains(r, 'href="/wishlist/"')
        self.assertEqual(self.client.get('/wishlist/').status_code, 200)

    def test_disabled_hides_everything_letter_related(self):
        self.disable()
        r = self.client.get('/')
        self.assertNotContains(r, 'href="/wishlist/"')
        self.assertNotContains(r, 'Wyślij list')
        r = self.client.get('/wishlist/', follow=True)
        self.assertRedirects(r, '/register/')
        self.assertContains(r, 'Wysyłanie listów do Mikołaja jest w tym roku wyłączone.')
        # posting a letter is refused too
        self.client.post('/wishlist/', {'mail': 'x@x.pl'})
        from .models import WishlistFile
        self.assertEqual(WishlistFile.objects.count(), 0)

    def test_draw_mail_without_letter_links_when_disabled(self):
        from django.core import mail as outbox
        from .draw import send_draw_mail
        a, b = make_user(0), make_user(1)
        send_draw_mail(a, b)
        self.assertIn('/checkwishlist/', outbox.outbox[0].body)
        self.disable()
        send_draw_mail(a, b)
        self.assertNotIn('/checkwishlist/', outbox.outbox[1].body)
        self.assertNotIn('/wishlist/', outbox.outbox[1].body)
        self.assertIn('Zrób prezent dla: N1 S1', outbox.outbox[1].body)

    def test_toggle_in_panel(self):
        AuthUser.objects.create_user('boss', password='pw', is_staff=True)
        self.client.login(username='boss', password='pw')
        page = self.client.get('/admin/')
        self.assertContains(page, 'name="letters_enabled"')
        self.assertContains(page, 'Przypomnij o liście do Mikołaja')
        # unticked checkbox = letters off
        self.client.post('/admin/event/', {'party_host': 'Agnieszki', 'gift_budget': '50 zł', 'site_url': 'https://example.com'})
        self.assertFalse(SiteSettings.load().letters_enabled)
        self.assertNotContains(self.client.get('/admin/'), 'Przypomnij o liście do Mikołaja')
        self.client.post('/admin/event/', {'party_host': 'Agnieszki', 'gift_budget': '50 zł', 'site_url': 'https://example.com',
                                           'letters_enabled': 'on'})
        self.assertTrue(SiteSettings.load().letters_enabled)


class SiteTitleTests(TestCase):
    def test_title_follows_letters_switch(self):
        r = self.client.get('/')
        self.assertContains(r, '<title>Rejestracja · List do Mikołaja</title>')
        self.assertContains(r, 'class="logo" href="/register/">List do Mikołaja</a>')
        s = SiteSettings.load()
        s.letters_enabled = False
        s.save()
        r = self.client.get('/')
        self.assertContains(r, '<title>Rejestracja · Zostań Mikołajem</title>')
        self.assertContains(r, 'class="logo" href="/register/">Zostań Mikołajem</a>')
        self.assertNotContains(r, 'List do Mikołaja')
        self.client.post('/i18n/setlang/', {'language': 'en', 'next': '/'})
        self.assertContains(self.client.get('/'), 'class="logo" href="/register/">Become Santa</a>')
