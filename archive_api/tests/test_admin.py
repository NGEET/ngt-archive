import os

from django.contrib.auth.models import User
from django.test import TestCase
from django.test import Client

BASE_PATH = os.path.dirname(os.path.realpath(__file__))


class DownloadLogAdminTestCase(TestCase):
    fixtures = ['test_auth.json', 'test_archive_api.json',
                'test_downloadlog.json']

    @staticmethod
    def login(username):
        """
        Login helper methods

        :param username: username to login
        :return:
        """
        client = Client()
        user = User.objects.get(username=username)
        client.force_login(user)
        return client

    def test_view(self):
        """
        Assert that download log admin page is accessible

        """

        client = self.login("superadmin")

        response = client.get("/admin/archive_api/datasetdownloadlog/", follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "text/html; charset=utf-8")
