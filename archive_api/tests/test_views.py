from __future__ import print_function, unicode_literals

import json

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APIRequestFactory, APITestCase, force_authenticate
from archive_api.viewsets import DataSetViewSet


class DataSetTestCase(APITestCase):
    fixtures = ('test_db.json',)

    def setUp(self):
        self.user = User.objects.get(username='vagrant')
        self.view_list = DataSetViewSet.as_view({'get': 'list'})
        self.view_detail = DataSetViewSet.as_view({'get': 'retrieve'})

    def test_get_list(self):
        """
        Ensure list the parameters option.
        """

        # Using the standard RequestFactory API to create a form POST request
        factory = APIRequestFactory()
        request = factory.get('api/v1/datasets')
        force_authenticate(request,self.user)
        response = self.view_list(request)
        response.render()  # Cannot access `response.content` without this.
        self.assertEqual(json.loads(response.content.decode('utf-8')),
                         [{"url": "http://testserver/api/v1/datasets/1/", "dataSetId": "Foo",
                           "description": "A Foo DataSet"},
                          {"url": "http://testserver/api/v1/datasets/2/", "dataSetId": "Bar",
                           "description": "A Bar DataSet"}])
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_detail(self):
        """
        Ensure get the parameter option.
        """

        # Using the standard RequestFactory API to create a form POST request
        factory = APIRequestFactory()
        request = factory.get('api/v1/datasets/1')
        force_authenticate(request,self.user)
        response = self.view_detail(request, pk='1')
        response.render()  # Cannot access `response.content` without this.
        self.assertEqual(json.loads(response.content.decode('utf-8')),
                         {"url": "http://testserver/api/v1/datasets/1/", "dataSetId": "Foo",
                          "description": "A Foo DataSet"})
