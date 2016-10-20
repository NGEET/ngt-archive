from __future__ import print_function, unicode_literals

import json

from django.contrib.auth.models import User
from django.test import Client
from django.test.client import encode_multipart, MULTIPART_CONTENT, BOUNDARY
from rest_framework import status
from rest_framework.test import APITestCase


class DataSetClientTestCase(APITestCase):
    fixtures = ('test_db.json',)

    def setUp(self):
        self.client = Client()
        user = User.objects.get(username="valerie")
        self.client.force_login(user)

    def test_cliet_get_root(self):
        response = self.client.get('/api/v1/')
        self.assertEqual(json.loads(response.content.decode('utf-8')),
                         {"datasets": "http://testserver/api/v1/datasets/"})

    def test_cliet_list_datasets(self):
        response = self.client.get('/api/v1/datasets/')
        self.assertEqual(json.loads(response.content.decode('utf-8')),
                         [{"url": "http://testserver/api/v1/datasets/1/", "dataSetId": "Foo",
                           "description": "A Foo DataSet"},
                          {"url": "http://testserver/api/v1/datasets/2/", "dataSetId": "Bar",
                           "description": "A Bar DataSet"}])
        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_cliet_get_dataset(self):
        response = self.client.get('/api/v1/datasets/2/')
        self.assertEqual(json.loads(response.content.decode('utf-8')),
                         {"url": "http://testserver/api/v1/datasets/2/", "dataSetId": "Bar",
                          "description": "A Bar DataSet"})
        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_cliet_post_dataset(self):
        response = self.client.post('/api/v1/datasets/',
                                    data='{"dataSetId":"FooBarBaz","description":"A FooBarBaz DataSet"}',
                                   content_type='application/json')
        self.assertEqual(json.loads(response.content.decode('utf-8')),
                         {"url": "http://testserver/api/v1/datasets/3/", "dataSetId": "FooBarBaz",
                          "description": "A FooBarBaz DataSet"})
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

    def test_cliet_put_dataset(self):
        response = self.client.put('/api/v1/datasets/2/',
                                   data='{"dataSetId":"FooBarBaz","description":"A FooBarBaz DataSet"}',
                                   content_type='application/json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        response = self.client.get('/api/v1/datasets/2/')
        self.assertEqual(json.loads(response.content.decode('utf-8')),
                         {"url": "http://testserver/api/v1/datasets/2/", "dataSetId": "FooBarBaz",
                          "description": "A FooBarBaz DataSet"})