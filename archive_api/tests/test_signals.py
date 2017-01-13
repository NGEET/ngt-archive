from django.contrib.auth.models import User
from django.core import mail
from django.test import Client
from django.test import TestCase


class TestLoginSignals(TestCase):
    fixtures = ('test_auth.json', 'test_archive_api.json', )

    def setUp(self):
        self.client = Client()

    def test_signal_add_user_to_group(self):

        user = User.objects.get(username="lukecage")

        self.assertEqual(len(user.groups.all()),0)
        self.client.force_login(user)

        self.assertEqual(len(user.groups.all()), 1)
        self.assertEqual(user.groups.first().name,"NGT Team")
        self.assertEqual(len(mail.outbox), 0)

    def test_signal_notify_no_person(self):
        user = User.objects.get(username="flash")

        self.assertEqual(len(user.groups.all()), 0)
        self.client.force_login(user)

        self.assertEqual(len(user.groups.all()), 0)
        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]

        self.assertEqual(email.to, ['ngee-tropics-archive@googlegroups.com'])
        self.assertEqual(email.reply_to, ['ngee-tropics-archive@googlegroups.com'])
        self.assertTrue(email.subject, "[ngt-archive] Barry Allen requesting activation")
        self.assertTrue(email.body.find("User Barry Allen is requesting access to NGEE Tropics Archive service.") > -1)

    def test_signal_notify(self):
        user = User.objects.get(username="vibe")

        self.assertEqual(len(user.groups.all()),0)
        self.client.force_login(user)

        self.assertEqual(len(user.groups.all()), 0)
        self.assertEqual(len(mail.outbox),1)

        email = mail.outbox[0]

        self.assertEqual(email.to,['ngee-tropics-archive@googlegroups.com'])
        self.assertEqual(email.reply_to, ['ngee-tropics-archive@googlegroups.com'])
        self.assertTrue(email.subject, "[ngt-archive] Cisco Ramon requesting activation")
        self.assertTrue(email.body.find("User Cisco Ramon is requesting access to NGEE Tropics Archive service.")>-1)

