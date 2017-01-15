from django.contrib.auth.models import User
from django.core import mail
from django.test import Client
from django.test import TestCase
from django.test import override_settings

from archive_api.models import Person


@override_settings(ARCHIVE_API_EMAIL_NGEET_TEAM='ngeet-team@testserver',
                   ARCHIVE_API_EMAIL_SUBJECT_PREFIX='[ngt-archive-test]')
class TestLoginSignals(TestCase):
    fixtures = ('test_auth.json', 'test_archive_api.json',)

    def setUp(self):
        self.client = Client()

    def test_signal_add_user_to_group(self):
        user = User.objects.get(username="lukecage")

        self.assertEqual(len(user.groups.all()), 0)
        self.client.force_login(user)

        self.assertEqual(len(user.groups.all()), 1)
        self.assertEqual(user.groups.first().name, "NGT Team")
        self.assertEqual(len(mail.outbox), 0)

        # The user object should have been assinged to the user
        person = Person.objects.get(email="lcage@foobar.baz")
        self.assertIsNotNone(person)
        self.assertEqual(user, person.user)

    def test_signal_notify_no_person(self):
        user = User.objects.get(username="flash")

        self.assertEqual(len(user.groups.all()), 0)
        self.client.force_login(user)

        self.assertEqual(len(user.groups.all()), 0)
        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]

        self.assertEqual(email.to, ['ngeet-team@testserver'])
        self.assertEqual(email.reply_to, ['ngeet-team@testserver'])
        self.assertTrue(email.subject, "[ngt-archive-test] Barry Allen requesting activation")
        self.assertTrue(email.body.find("User Barry Allen is requesting access to NGEE Tropics Archive service.") > -1)

    def test_signal_notify(self):
        user = User.objects.get(username="vibe")

        self.assertEqual(len(user.groups.all()), 0)
        self.client.force_login(user)

        self.assertEqual(len(user.groups.all()), 0)
        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]

        self.assertEqual(email.to, ['ngeet-team@testserver'])
        self.assertEqual(email.reply_to, ['ngeet-team@testserver'])
        self.assertTrue(email.subject, "[ngt-archive-test] Cisco Ramon requesting activation")
        self.assertTrue(email.body.find("User Cisco Ramon is requesting access to NGEE Tropics Archive service.") > -1)
