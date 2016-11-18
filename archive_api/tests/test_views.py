from __future__ import print_function, unicode_literals

import json

from archive_api.viewsets import DataSetViewSet
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APIRequestFactory, APITestCase, force_authenticate


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
        self.assertAlmostEqual(len(json.loads(response.content.decode('utf-8'))), 3)
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
        value = json.loads(response.content.decode('utf-8'))
        self.assertEqual(value['url'], "http://testserver/api/v1/datasets/1/")
        self.assertEqual(value["status"], "0")
        self.assertEqual(value["description"],
                         "Lorem ipsum dolor sit amet, impedit accusamus reprehendunt in quo, accusata voluptaria scribentur te nec. Id mel partem euismod bonorum. No modus dolore vim, per in exerci iisque persequeris, animal interesset sit ex. Vero ocurreret nam an.")
        self.assertEqual(value["statusComment"], "")
        self.assertEqual(value["doi"], "")
        self.assertEqual(value["startDate"], "2016-10-28")
        self.assertEqual(value["endDate"], None)
        self.assertEqual(value["qaqcStatus"], None)
        self.assertEqual(value["qaqcMethodDescription"], "")
        self.assertEqual(value["ngeeTropicsResources"], True)
        self.assertEqual(value["fundingOrganizations"], "")
        self.assertEqual(value["doeFundingContractNumbers"], "")
        self.assertEqual(value["acknowledgement"], "")
        self.assertEqual(value["reference"], "")
        self.assertEqual(value["additionalReferenceInformation"], "")
        self.assertEqual(value["accessLevel"], "0")
        self.assertEqual(value["additionalAccessInformation"], "")
        self.assertEqual(value["submissionDate"], None)
        self.assertEqual(value["contact"], "http://testserver/api/v1/people/2/")
        self.assertEqual(value["sites"], [
            "http://testserver/api/v1/sites/1/"
        ])
        self.assertEqual(value["plots"], [
            "http://testserver/api/v1/plots/1/"
        ])
        self.assertEqual(value["variables"], [
            "http://testserver/api/v1/variables/1/",
            "http://testserver/api/v1/variables/2/"
        ])
        self.assertEqual(value["createdBy"], "auser")
        self.assertEqual(value["modifiedBy"], "auser")
