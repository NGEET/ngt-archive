from __future__ import print_function, unicode_literals

import json

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APIRequestFactory, APITestCase, force_authenticate

from archive_api.viewsets import DataSetViewSet


class DataSetTestCase(APITestCase):
    fixtures = ('test_archive_api.json', 'test_auth.json',)

    def setUp(self):
        self.user = User.objects.get(username='admin')
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
                         [
                             {
                                 "url": "http://testserver/api/v1/datasets/1/",
                                 "dataSetId": "DS-1",
                                 "description": "Lorem ipsum dolor sit amet, impedit accusamus reprehendunt in quo, accusata voluptaria scribentur te nec. Id mel partem euismod bonorum. No modus dolore vim, per in exerci iisque persequeris, animal interesset sit ex. Vero ocurreret nam an."
                             },
                             {
                                 "url": "http://testserver/api/v1/datasets/2/",
                                 "dataSetId": "DS-2",
                                 "description": "Qui illud verear persequeris te. Vis probo nihil verear an, zril tamquam philosophia eos te, quo ne fugit movet contentiones. Quas mucius detraxit vis an, vero omnesque petentium sit ea. Id ius inimicus comprehensam."
                             }
                         ])
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
                         {
                             "url": "http://testserver/api/v1/datasets/1/",
                             "dataSetId": "DS-1",
                             "description": "Lorem ipsum dolor sit amet, impedit accusamus reprehendunt in quo, accusata voluptaria scribentur te nec. Id mel partem euismod bonorum. No modus dolore vim, per in exerci iisque persequeris, animal interesset sit ex. Vero ocurreret nam an."
                         })
