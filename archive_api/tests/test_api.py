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
                          "people": "http://testserver/api/v1/people/",
                          "plots": "http://testserver/api/v1/plots/"})


class DataSetClientTestCase(APITestCase):
    fixtures = ('test_archive_api.json', 'test_auth.json',)

    def login_user(self, username):
        user = User.objects.get(username=username)
        self.client.force_login(user)

    def setUp(self):
        self.client = Client()

    def test_client_list(self):
        self.login_user("auser")
        response = self.client.get('/api/v1/datasets/')
        self.assertEqual(len(json.loads(response.content.decode('utf-8'))),
                         2)
        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_client_get(self):
        self.login_user("auser")
        response = self.client.get('/api/v1/datasets/2/')
        value = json.loads(response.content.decode('utf-8'))
        self.assertEqual(value,
                         {'contact': 'http://testserver/api/v1/people/2/', 'owner': 'auser', 'name': 'Data Set 2',
                          'startDate': '2016-10-28', 'acknowledgement': '',
                          'createdDate': '2016-10-28T19:15:35.013361Z', 'sites': ['http://testserver/api/v1/sites/1/'],
                          'qaqcStatus': None, 'plots': ['http://testserver/api/v1/plots/1/'],
                          'doeFundingContractNumbers': '', 'status': '1', 'accessLevel': '0',
                          'fundingOrganizations': 'A few funding organizations', 'endDate': None,
                          'submissionDate': '2016-10-28T19:12:35Z',
                          'submissionContact': {'firstName': 'Merry', 'lastName': 'Yuser', 'email': 'myuser@foo.bar'},
                          'variables': ['http://testserver/api/v1/variables/1/',
                                        'http://testserver/api/v1/variables/2/',
                                        'http://testserver/api/v1/variables/3/'], 'additionalAccessInformation': '',
                          'modifiedDate': '2016-10-28T23:01:20.066913Z', 'reference': '',
                          'authors': ["http://testserver/api/v1/people/2/"],
                          'modifiedBy': 'auser', 'ngeeTropicsResources': True,
                          'url': 'http://testserver/api/v1/datasets/2/', 'statusComment': '',
                          'qaqcMethodDescription': '', 'additionalReferenceInformation': '', 'doi': '',
                          'description': 'Qui illud verear persequeris te. Vis probo nihil verear an, zril tamquam philosophia eos te, quo ne fugit movet contentiones. Quas mucius detraxit vis an, vero omnesque petentium sit ea. Id ius inimicus comprehensam.'}

                         )

        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_client_post(self):
        self.login_user("auser")
        response = self.client.post('/api/v1/datasets/',
                                    data='{"dataSetId":"FooBarBaz","description":"A FooBarBaz DataSet"}',
                                    content_type='application/json')
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        value = json.loads(response.content.decode('utf-8'))
        self.assertEqual(value['accessLevel'], '0')
        self.assertEqual(value['sites'], [])
        self.assertEqual(value['owner'], 'auser')
        self.assertEqual(value['endDate'], None)
        self.assertEqual(value['doeFundingContractNumbers'], None)
        self.assertEqual(value['fundingOrganizations'], None)
        self.assertEqual(value['description'], 'A FooBarBaz DataSet')
        self.assertEqual(value['submissionContact'],
                         {'firstName': 'Merry', 'lastName': 'Yuser', 'email': 'myuser@foo.bar'})
        self.assertEqual(value['additionalAccessInformation'], None)
        self.assertEqual(value['name'], None)
        self.assertEqual(value['modifiedBy'], 'auser')
        self.assertEqual(value['ngeeTropicsResources'], False)
        self.assertEqual(value['status'], '0')
        self.assertEqual(value['doi'], None)
        self.assertEqual(value['plots'], [])
        self.assertEqual(value['contact'], None)
        self.assertEqual(value['reference'], None)
        self.assertEqual(value['variables'], [])
        self.assertEqual(value['additionalReferenceInformation'], None)
        self.assertEqual(value['startDate'], None)
        self.assertEqual(value['acknowledgement'], None)
        self.assertEqual(value['statusComment'], None)
        self.assertEqual(value['submissionDate'], None)
        self.assertEqual(value['qaqcStatus'], None)
        self.assertEqual(value['url'], 'http://testserver/api/v1/datasets/3/')
        self.assertEqual(value['qaqcMethodDescription'], None)

        # The submit action should fail
        response = self.client.post('/api/v1/datasets/3/submit/')
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

        value = json.loads(response.content.decode('utf-8'))
        self.assertEqual({'missingRequiredFields': ['sites', 'authors',
                                                    'name', 'contact',
                                                    'variables',
                                                    'ngee_tropics_resources', 'funding_organizations']}, value)

    def test_client_put(self):
        self.login_user("auser")
        response = self.client.put('/api/v1/datasets/1/',
                                   data='{"dataSetId":"FooBarBaz","description":"A FooBarBaz DataSet",'
                                        '"name": "Data Set 1", '
                                        '"statusComment": "",'
                                        '"doi": "",'
                                        '"startDate": "2016-10-28",'
                                        '"endDate": null,'
                                        '"qaqcStatus": null,'
                                        '"qaqcMethodDescription": "",'
                                        '"ngeeTropicsResources": true,'
                                        '"fundingOrganizations": "",'
                                        '"doeFundingContractNumbers": "",'
                                        '"acknowledgement": "",'
                                        '"reference": "",'
                                        '"additionalReferenceInformation": "",'
                                        '"additionalAccessInformation": "",'
                                        '"submissionDate": "2016-10-28T19:12:35Z",'
                                        '"contact": "http://0.0.0.0:8888/api/v1/people/4/",'
                                        '"authors": ["http://0.0.0.0:8888/api/v1/people/1/"],'
                                        '"sites": ["http://0.0.0.0:8888/api/v1/sites/1/"],'
                                        '"plots": ["http://0.0.0.0:8888/api/v1/plots/1/"],'
                                        '"variables": ["http://0.0.0.0:8888/api/v1/variables/1/", '
                                        '"http://0.0.0.0:8888/api/v1/variables/2/"]}',
                                   content_type='application/json')

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        response = self.client.get('/api/v1/datasets/1/')
        value = json.loads(response.content.decode('utf-8'))
        self.assertEqual(value['description'], "A FooBarBaz DataSet")

    def test_user_workflow(self):
        """
        Test dataset workflow for an NGT User
        :return:
        """
        self.login_user("auser")

        #########################################################################
        # A dataset in submitted mode may not be submitted
        response = self.client.get("/api/v1/datasets/2/submit/")  # In submitted mode, owned by auser
        value = json.loads(response.content.decode('utf-8'))
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertEqual({'detail': 'You do not have permission to perform this action.'}, value)

        #########################################################################
        # NGT User may not APPROVE a dataset
        response = self.client.get("/api/v1/datasets/1/approve/")  # In draft mode, owned by auser
        value = json.loads(response.content.decode('utf-8'))
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertEqual({'detail': 'You do not have permission to perform this action.'}, value)

        #########################################################################
        # NGT User may not APPROVE a dataset
        response = self.client.get("/api/v1/datasets/2/approve/")  # In submitted mode, owned by auser
        value = json.loads(response.content.decode('utf-8'))
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertEqual({'detail': 'You do not have permission to perform this action.'}, value)

        #########################################################################
        # NGT User may edit a dataset in DRAFT mode if they own it
        response = self.client.get("/api/v1/datasets/1/submit/")  # In draft mode, owned by auser
        value = json.loads(response.content.decode('utf-8'))
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertEqual({'missingRequiredFields': ['authors', 'funding_organizations']}, value)

        response = self.client.put('/api/v1/datasets/1/',
                                   data='{"dataSetId":"FooBarBaz","description":"A FooBarBaz DataSet",'
                                        '"name": "Data Set 1", '
                                        '"statusComment": "",'
                                        '"doi": "",'
                                        '"startDate": "2016-10-28",'
                                        '"endDate": null,'
                                        '"qaqcStatus": null,'
                                        '"qaqcMethodDescription": "",'
                                        '"ngeeTropicsResources": true,'
                                        '"fundingOrganizations": "The funding organizations for my dataset",'
                                        '"doeFundingContractNumbers": "",'
                                        '"acknowledgement": "",'
                                        '"reference": "",'
                                        '"additionalReferenceInformation": "",'
                                        '"additionalAccessInformation": "",'
                                        '"submissionDate": "2016-10-28T19:12:35Z",'
                                        '"contact": "http://0.0.0.0:8888/api/v1/people/4/",'
                                        '"authors": ["http://0.0.0.0:8888/api/v1/people/1/"],'
                                        '"sites": ["http://0.0.0.0:8888/api/v1/sites/1/"],'
                                        '"plots": ["http://0.0.0.0:8888/api/v1/plots/1/"],'
                                        '"variables": ["http://0.0.0.0:8888/api/v1/variables/1/", '
                                        '"http://0.0.0.0:8888/api/v1/variables/2/"]}',
                                   content_type='application/json')

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        #########################################################################
        # NGT User may not SUBMIT a dataset in DRAFT mode if they owne it
        response = self.client.get("/api/v1/datasets/1/submit/")  # In draft mode, owned by auser
        value = json.loads(response.content.decode('utf-8'))
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual({'detail': 'DataSet has been submitted.', 'success': True}, value)

        #########################################################################
        # NGT User may not unsubmit a dataset
        response = self.client.get("/api/v1/datasets/1/unsubmit/")  # In draft mode, owned by auser
        value = json.loads(response.content.decode('utf-8'))
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertEqual({'detail': 'You do not have permission to perform this action.'}, value)

    def test_admin_approve_workflow(self):
        """
        Test Admin dataset workflow
        :return:
        """
        self.login_user("admin")

        #########################################################################
        # NGT Administrator my edit any DRAFT status (this will fail due to missing fields)
        response = self.client.get("/api/v1/datasets/1/submit/")  # In draft mode, owned by auser
        value = json.loads(response.content.decode('utf-8'))
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertEqual({'missingRequiredFields': ['authors', 'funding_organizations']}, value)

        #########################################################################
        # Cannot submit a dataset that it already in SUBMITTED status
        response = self.client.get("/api/v1/datasets/2/submit/")  # In submitted mode, owned by auser
        value = json.loads(response.content.decode('utf-8'))
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertEqual({'detail': 'You do not have permission to perform this action.'}, value)

        #########################################################################
        # NGT Administrator may edit a dataset in SUBMITTED status
        response = self.client.put('/api/v1/datasets/2/',
                                   data='{"dataSetId":"FooBarBaz","description":"A FooBarBaz DataSet",'
                                        '"name": "Data Set 2", '
                                        '"statusComment": "",'
                                        '"doi": "",'
                                        '"startDate": "2016-10-28",'
                                        '"endDate": null,'
                                        '"qaqcStatus": null,'
                                        '"qaqcMethodDescription": "",'
                                        '"ngeeTropicsResources": true,'
                                        '"fundingOrganizations": "The funding organizations for my dataset",'
                                        '"doeFundingContractNumbers": "",'
                                        '"acknowledgement": "",'
                                        '"reference": "",'
                                        '"accessLevel": "0",'
                                        '"additionalReferenceInformation": "",'
                                        '"additionalAccessInformation": "",'
                                        '"submissionDate": "2016-10-28T19:12:35Z",'
                                        '"contact": "http://0.0.0.0:8888/api/v1/people/4/",'
                                        '"authors": ["http://0.0.0.0:8888/api/v1/people/4/"],'
                                        '"sites": ["http://0.0.0.0:8888/api/v1/sites/1/"],'
                                        '"plots": ["http://0.0.0.0:8888/api/v1/plots/1/"],'
                                        '"variables": ["http://0.0.0.0:8888/api/v1/variables/1/", '
                                        '"http://0.0.0.0:8888/api/v1/variables/2/"]}',
                                   content_type='application/json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        #########################################################################
        # A dataset that is not in SUBMITTED status may not be approved
        response = self.client.get("/api/v1/datasets/1/approve/")  # In draft mode, owned by auser
        value = json.loads(response.content.decode('utf-8'))
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertEqual({'detail': 'You do not have permission to perform this action.'}, value)

        #########################################################################
        # NGT Administrator my APPROVE a SUBMITTED dataset
        response = self.client.get("/api/v1/datasets/2/approve/")  # In submitted mode, owned by auser
        value = json.loads(response.content.decode('utf-8'))
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual({'detail': 'DataSet has been approved.', 'success': True}, value)

        #########################################################################
        # APPROVED status: Cannot be deleted by anyone
        response = self.client.delete("/api/v1/datasets/2/")  # In submitted mode, owned by auser
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

        response = self.client.get("/api/v1/datasets/2/")  # should be deleted
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        response = self.client.get("/api/v1/datasets/2/")
        value = json.loads(response.content.decode('utf-8'))
        self.assertEqual(value['status'], '2')

        #########################################################################
        # NGT Administrator can put a dataset back into DRAFT status for corrections by the Owning NGT user
        response = self.client.get("/api/v1/datasets/2/unsubmit/")  # In draft mode, owned by auser
        value = json.loads(response.content.decode('utf-8'))
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertEqual({'detail': 'You do not have permission to perform this action.'}, value)

        response = self.client.get("/api/v1/datasets/2/unapprove/")  # In approved mode, owned by auser
        value = json.loads(response.content.decode('utf-8'))
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual({'detail': 'DataSet has been unapproved.', 'success': True}, value)

        #########################################################################
        # NGT Administrator my unapproved a dataset (put back into submitted mode)
        response = self.client.get("/api/v1/datasets/1/unapprove/")  # In approved mode, owned by auser
        value = json.loads(response.content.decode('utf-8'))
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertEqual({'detail': 'You do not have permission to perform this action.'}, value)
        response = self.client.get("/api/v1/datasets/2/")  # Check the status
        value = json.loads(response.content.decode('utf-8'))
        self.assertEqual(value['status'], '1')

    def test_admin_unsubmit(self):
        """
        Test Admin unsubmit
        :return:
        """
        self.login_user("admin")

        #########################################################################
        # Adn admin may unsubmit a dataset in SUBIMITTED MODE
        response = self.client.get("/api/v1/datasets/2/unsubmit/")  # In submitted mode, owned by auser
        value = json.loads(response.content.decode('utf-8'))
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual({'detail': 'DataSet has been unsubmitted.', 'success': True}, value)

        response = self.client.get("/api/v1/datasets/2/")
        value = json.loads(response.content.decode('utf-8'))
        self.assertEqual(value['status'], '0')  # check that the status is in DRAFT

    def test_user_delete(self):
        """
        Test Admin delete
        :return:
        """
        self.login_user("auser")

        #########################################################################
        # NGT User may not delete a SUBMITTED dataset
        response = self.client.delete("/api/v1/datasets/2/")  # In submitted mode, owned by auser
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

        # Confirm that it wasn't deleted
        response = self.client.get("/api/v1/datasets/2/")  # should be deleted
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        #########################################################################
        # NGT user may delete a DRAFT dataset
        response = self.client.delete("/api/v1/datasets/1/")  # In submitted mode, owned by auser
        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)

        response = self.client.get("/api/v1/datasets/1/")  # should be deleted
        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)

    def test_admin_delete(self):
        """
        Test Admin delete
        :return:
        """
        self.login_user("admin")

        #########################################################################
        # NGT User may  delete a SUBMITTED dataset
        response = self.client.delete("/api/v1/datasets/2/")  # In submitted mode, owned by auser
        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)

        response = self.client.get("/api/v1/datasets/2/")  # should be deleted
        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)

        #########################################################################
        # NGT User may delete a DRAFT dataset
        response = self.client.delete("/api/v1/datasets/1/")  # In submitted mode, owned by auser
        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)

        response = self.client.get("/api/v1/datasets/1/")  # should be deleted
        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)


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
                          "submissionDate": "2016-10-01", "contacts": [], "pis": [],
                          "submission": "http://testserver/api/v1/people/3/"})
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
                          "pi": "http://testserver/api/v1/people/3/",
                          "site": "http://testserver/api/v1/sites/1/",
                          "submission": "http://testserver/api/v1/people/4/"})
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
        response = self.client.get('/api/v1/people/')
        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_client_get(self):
        response = self.client.get('/api/v1/people/2/')
        self.assertEqual(json.loads(response.content.decode('utf-8')),
                         {"url": "http://testserver/api/v1/people/2/", "firstName": "Luke",
                          "lastName": "Cage", "email": "lcage@foobar.baz", "institutionAffiliation": "POWER"})
        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_client_post(self):
        response = self.client.post('/api/v1/people/',
                                    data='{"firstName":"Killer","lastName":"Frost","email":"kfrost@earth2.baz","institutionAffiliation":"ZOOM"}',
                                    content_type='application/json')
        self.assertEqual(json.loads(response.content.decode('utf-8')),
                         {"url": "http://testserver/api/v1/people/6/", "firstName": "Killer", "lastName": "Frost",
                          "email": "kfrost@earth2.baz", "institutionAffiliation": "ZOOM"})
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

    def test_client_put(self):
        response = self.client.put('/api/v1/people/2/',
                                   data='{"url": "http://testserver/api/v1/people/2/", "firstName": "Luke", "lastName": "Cage", "email": "lcage@foobar.baz", "institutionAffiliation": "POW"}',
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
