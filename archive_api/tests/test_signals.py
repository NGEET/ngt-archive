from django.contrib.auth.models import User
from django.core import mail
from django.test import Client
from django.test import TestCase
from django.test import override_settings
from archive_api.models import Person


@override_settings(EMAIL_NGEET_TEAM='ngeet-team@testserver',
                   EMAIL_SUBJECT_PREFIX='[ngt-archive-test]')
class TestLoginSignals(TestCase):
    fixtures = ('test_auth.json', 'test_archive_api.json',)

    def setUp(self):
        self.client = Client()

    def test_signal_user_banned(self):
        user = User.objects.get(username="lukecage")
        self.assertEqual(user.is_active, False)

        self.client.force_login(user)

        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(user.is_active, False)

    def test_signal_add_user_to_group(self):
        user = User.objects.get(username="lukecage")
        self.assertEqual(user.is_active,False)
        user.is_active=True
        user.save()

        self.assertEqual(len(user.groups.all()), 0)
        self.client.force_login(user)

        self.assertEqual(len(user.groups.all()), 1)
        self.assertEqual(user.groups.first().name, "NGT Team")
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(user.is_active, True)

        # The user object should have been assinged to the user
        person = Person.objects.get(email="lcage@foobar.baz")
        self.assertIsNotNone(person)
        self.assertEqual(user, person.user)

    def test_signal_notify_no_person(self):
        user = User.objects.get(username="flash")

        self.assertEqual(user.is_active, False)

        self.assertEqual(len(user.groups.all()), 0)
        self.client.force_login(user)

        self.assertEqual(len(user.groups.all()), 0)
        self.assertEqual(len(mail.outbox), 1)

        self.assertEqual(user.is_active, True)

        email = mail.outbox[0]

        self.assertEqual(email.to, [user.email])
        self.assertEqual(email.cc, ['NGEE Tropics Archive Test <ngeet-team@testserver>'])
        self.assertEqual(email.reply_to, ['NGEE Tropics Archive Test <ngeet-team@testserver>'])
        self.assertEqual(email.subject, "[ngt-archive-test] NGEE-Tropics Account Created for 'flash'")
        self.assertTrue(email.body.find("Greetings flash") > -1)

    def test_signal_notify_no_person_last_login(self):
        user = User.objects.get(username="arrow")

        self.assertEqual(user.is_active, True)
        self.assertNotEqual(user.last_login, None)

        self.assertEqual(len(user.groups.all()), 0)
        self.client.force_login(user)

        self.assertEqual(len(user.groups.all()), 0)
        self.assertEqual(len(mail.outbox), 0)

        self.assertEqual(user.is_active, True)

    def test_signal_notify(self):
        user = User.objects.get(username="vibe")

        self.assertEqual(user.is_active,True)
        self.assertEqual(user.last_login, None)

        self.assertEqual(len(user.groups.all()), 0)
        self.client.force_login(user)

        self.assertEqual(len(user.groups.all()), 0)
        self.assertEqual(len(mail.outbox), 1)

        self.assertEqual(user.is_active, True)

        email = mail.outbox[0]

        self.assertEqual(email.to, [user.email])
        self.assertEqual(email.cc, ['NGEE Tropics Archive Test <ngeet-team@testserver>'])
        self.assertEqual(email.reply_to, ['NGEE Tropics Archive Test <ngeet-team@testserver>'])
        self.assertEqual(email.subject, "[ngt-archive-test] NGEE-Tropics Account Created for 'vibe'")
        self.assertTrue(email.body.find("Greetings vibe,") > -1)

    def test_signal_no_notify(self):
        user = User.objects.get(username="superadmin")

        self.assertEqual(user.is_active,True)

        self.assertEqual(len(user.groups.all()), 0)
        self.client.force_login(user)

        self.assertEqual(len(user.groups.all()), 0)
        self.assertEqual(len(mail.outbox), 0)
