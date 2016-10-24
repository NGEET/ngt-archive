from __future__ import print_function, unicode_literals

import json

from django.contrib.auth.models import User
from django.test import Client
from rest_framework import status
from rest_framework.test import APITestCase


class ApiRootClientTestCase(APITestCase):
    fixtures = ('test_archive_api.json', 'test_auth.json',)

    def setUp(self):
        self.client = Client()
        user = User.objects.get(username="auser")
        self.client.force_login(user)

    def test_client_get_root(self):
        response = self.client.get('/api/v1/')
        self.assertEqual(json.loads(response.content.decode('utf-8')),
                         {"datasets": "http://testserver/api/v1/datasets/",
                          "sites": "http://testserver/api/v1/sites/",
                          "variables": "http://testserver/api/v1/variables/",
                          "contacts": "http://testserver/api/v1/contacts/",
                          "plots": "http://testserver/api/v1/plots/"})


class DataSetClientTestCase(APITestCase):
    fixtures = ('test_archive_api.json', 'test_auth.json',)

    def setUp(self):
        self.client = Client()
        user = User.objects.get(username="auser")
        self.client.force_login(user)

    def test_client_list(self):
        response = self.client.get('/api/v1/datasets/')
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
        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_client_get(self):
        response = self.client.get('/api/v1/datasets/2/')
        self.assertEqual(json.loads(response.content.decode('utf-8')),
                         {"url": "http://testserver/api/v1/datasets/2/", "dataSetId": "DS-2",
                          "description": "Qui illud verear persequeris te. Vis probo nihil verear an, zril tamquam philosophia eos te, quo ne fugit movet contentiones. Quas mucius detraxit vis an, vero omnesque petentium sit ea. Id ius inimicus comprehensam."})
        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_client_post(self):
        response = self.client.post('/api/v1/datasets/',
                                    data='{"dataSetId":"FooBarBaz","description":"A FooBarBaz DataSet"}',
                                    content_type='application/json')
        self.assertEqual(json.loads(response.content.decode('utf-8')),
                         {"url": "http://testserver/api/v1/datasets/3/", "dataSetId": "FooBarBaz",
                          "description": "A FooBarBaz DataSet"})
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

    def test_client_put(self):
        response = self.client.put('/api/v1/datasets/2/',
                                   data='{"dataSetId":"FooBarBaz","description":"A FooBarBaz DataSet"}',
                                   content_type='application/json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        response = self.client.get('/api/v1/datasets/2/')
        self.assertEqual(json.loads(response.content.decode('utf-8')),
                         {"url": "http://testserver/api/v1/datasets/2/", "dataSetId": "FooBarBaz",
                          "description": "A FooBarBaz DataSet"})


class SiteClientTestCase(APITestCase):
    fixtures = ('test_archive_api.json', 'test_auth.json',)

    def setUp(self):
        self.client = Client()
        user = User.objects.get(username="auser")
        self.client.force_login(user)

    def test_client_list(self):
        response = self.client.get('/api/v1/sites/')
        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_client_get(self):
        response = self.client.get('/api/v1/sites/1/')
        self.assertEqual(json.loads(response.content.decode('utf-8')),
                         {"url": "http://testserver/api/v1/sites/1/", "siteId": "CC-CCPD",
                          "name": "Central City CCPD",
                          "description": "Et doming epicurei posidonium has, an sit sanctus intellegebat. Ne malis reprehendunt mea. Iisque dolorem vel cu. Ut nam sapientem appellantur definitiones, copiosae placerat inimicus per ei. Cu pro reque putant, cu perfecto urbanitas posidonium eum, pri probo laoreet cu. Ei duo cetero concludaturque, ei adhuc facilis sit.\r\n\r\nAn aeque harum ius, mea ut erant verear salutandi. Eligendi recusabo usu ad. Ad modo vero consequat his, ne aperiam alienum suscipiantur his. Altera laoreet petentium pro ut. His option vocibus at. Vix no semper omnesque maluisset, accusata qualisque ut pro. Eos sint constituto temporibus in.",
                          "country": "United States", "stateProvince": "", "utcOffset": -9,
                          "locationLatitude": -8.983987234, "locationLongitude": 5.9832932847,
                          "locationElevation": "100-400", "locationMapUrl": "", "locationBoundingBoxUlLatitude": None,
                          "locationBoundingBoxUlLongitude": None, "locationBoundingBoxLrLatitude": None,
                          "locationBoundingBoxLrLongitude": None, "siteUrls": "http://centralcityccpd.baz",
                          "submissionDate": "2016-10-01", "contact": None, "pi": None,
                          "submission": "http://testserver/api/v1/contacts/3/"})
        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_client_post(self):
        response = self.client.post('/api/v1/sites/',
                                    data='{"dataSetId":"FooBarBaz","description":"A FooBarBaz DataSet"}',
                                    content_type='application/json')
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_client_put(self):
        response = self.client.put('/api/v1/sites/2/',
                                   data='{"dataSetId":"FooBarBaz","description":"A FooBarBaz DataSet"}',
                                   content_type='application/json')
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)


class PlotClientTestCase(APITestCase):
    fixtures = ('test_archive_api.json', 'test_auth.json',)

    def setUp(self):
        self.client = Client()
        user = User.objects.get(username="auser")
        self.client.force_login(user)

    def test_client_list(self):
        response = self.client.get('/api/v1/plots/')
        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_client_get(self):
        response = self.client.get('/api/v1/plots/1/')
        self.assertEqual(json.loads(response.content.decode('utf-8')),
                         {"url": "http://testserver/api/v1/plots/1/", "plotId": "CC-CCPD1",
                          "name": "Central City CCPD Plot 1",
                          "description": "Sed ut perspiciatis, unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam eaque ipsa, quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt, explicabo. Nemo enim ipsam voluptatem, quia voluptas sit, aspernatur aut odit aut fugit, sed quia consequuntur magni dolores eos, qui ratione voluptatem sequi nesciunt, neque porro quisquam est, qui dolorem ipsum, quia dolor sit amet, consectetur, adipisci[ng] velit, sed quia non numquam [do] eius modi tempora inci[di]dunt, ut labore et dolore magnam aliquam quaerat voluptatem. Ut enim ad minima veniam, quis nostrum exercitationem ullam corporis suscipit laboriosam, nisi ut aliquid ex ea commodi consequatur? Quis autem vel eum iure reprehenderit, qui in ea voluptate velit esse, quam nihil molestiae consequatur, vel illum, qui dolorem eum fugiat, quo voluptas nulla pariatur",
                          "size": "", "locationElevation": "", "locationKmzUrl": "", "submissionDate": "2016-10-08",
                          "pi": "http://testserver/api/v1/contacts/3/",
                          "site": "http://testserver/api/v1/sites/1/",
                          "submission": "http://testserver/api/v1/contacts/4/"})
        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_client_post(self):
        response = self.client.post('/api/v1/plots/',
                                    data='{"dataSetId":"FooBarBaz","description":"A FooBarBaz DataSet"}',
                                    content_type='application/json')
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_client_put(self):
        response = self.client.put('/api/v1/plots/1/',
                                   data='{"dataSetId":"FooBarBaz","description":"A FooBarBaz DataSet"}',
                                   content_type='application/json')
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)


class ContactClientTestCase(APITestCase):
    fixtures = ('test_archive_api.json', 'test_auth.json',)

    def setUp(self):
        self.client = Client()
        user = User.objects.get(username="auser")
        self.client.force_login(user)

    def test_client_list(self):
        response = self.client.get('/api/v1/contacts/')
        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_client_get(self):
        response = self.client.get('/api/v1/contacts/2/')
        self.assertEqual(json.loads(response.content.decode('utf-8')),
                         {"url": "http://testserver/api/v1/contacts/2/", "firstName": "Luke",
                          "lastName": "Cage", "email": "lcage@foobar.baz", "institutionAffiliation": "POWER"})
        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_client_post(self):
        response = self.client.post('/api/v1/contacts/',
                                    data='{"firstName":"Killer","lastName":"Frost","email":"kfrost@earth2.baz","institutionAffiliation":"ZOOM"}',
                                    content_type='application/json')
        self.assertEqual(json.loads(response.content.decode('utf-8')),
                         {"url": "http://testserver/api/v1/contacts/6/", "firstName": "Killer", "lastName": "Frost",
                          "email": "kfrost@earth2.baz", "institutionAffiliation": "ZOOM"})
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

    def test_client_put(self):
        response = self.client.put('/api/v1/contacts/2/',
                                   data='{"url": "http://testserver/api/v1/contacts/2/", "firstName": "Luke", "lastName": "Cage", "email": "lcage@foobar.baz", "institutionAffiliation": "POW"}',
                                   content_type='application/json')
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)


class VariableClientTestCase(APITestCase):
    fixtures = ('test_archive_api.json', 'test_auth.json',)

    def setUp(self):
        self.client = Client()
        user = User.objects.get(username="auser")
        self.client.force_login(user)

    def test_client_list(self):
        response = self.client.get('/api/v1/variables/')
        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_client_get(self):
        response = self.client.get('/api/v1/variables/2/')
        self.assertEqual(json.loads(response.content.decode('utf-8')),
                         {"url": "http://testserver/api/v1/variables/2/", "name": "Ice"})
        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_client_post(self):
        response = self.client.post('/api/v1/variables/',
                                    data='{"name":"Val}',
                                    content_type='application/json')
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_client_put(self):
        response = self.client.put('/api/v1/variables/2/',
                                   data='", "{"name":"Val}"}',
                                   content_type='application/json')
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
