from __future__ import print_function, unicode_literals

import json
from unittest import mock
from unittest.mock import PropertyMock

import shutil
from django.contrib.auth.models import User
from django.core import mail
from django.test import Client
from django.test import override_settings
from os.path import dirname
from rest_framework import status
from rest_framework.test import APITestCase

from archive_api.models import DatasetArchiveField, DataSetDownloadLog
from ngt_archive import settings


# Mock methods
def get_max_size(size):
    """ Return a get_size method for the size given"""

    def get_size():
        return size
    return get_size()


class ApiRootClientTestCase(APITestCase):
    fixtures = ('test_auth.json', 'test_archive_api.json',)

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


@override_settings(EMAIL_NGEET_TEAM='ngeet-team@testserver',
                   EMAIL_SUBJECT_PREFIX='[ngt-archive-test]')
class DataSetClientTestCase(APITestCase):
    fixtures = ('test_auth.json', 'test_archive_api.json',)

    def login_user(self, username):
        user = User.objects.get(username=username)
        self.client.force_login(user)

    def setUp(self):
        self.client = Client()

    def test_client_list(self):

        # Unauthorized user that is not in any groups
        self.login_user("vibe")
        response = self.client.get('/api/v1/datasets/')
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

        self.login_user("auser")
        response = self.client.get('/api/v1/datasets/')
        self.assertEqual(len(json.loads(response.content.decode('utf-8'))),
                         2)
        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_options(self):
        self.login_user("auser")
        response = self.client.options('/api/v1/datasets/')
        self.assertContains(response, "detail_routes")
        self.assertContains(response, "allowed_mime_types")
        self.assertContains(response, "upload")
        self.assertContains(response, "submit")
        self.assertContains(response, "approve")
        self.assertContains(response, "unapprove")
        self.assertContains(response, "unsubmit")
        for mime_type in DatasetArchiveField.CONTENT_TYPES:
            self.assertContains(response, mime_type)

    def test_client_unnamed(self):

        self.login_user("auser")
        response = self.client.post('/api/v1/datasets/',
                                    data='{"description":"A FooBarBaz DataSet",'
                                         '"authors":["http://testserver/api/v1/people/2/"]  }',
                                    content_type='application/json')
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        dataset_url = json.loads(response.content.decode('utf-8'))["url"]

        with open('{}/Archive.zip'.format(dirname(__file__)), 'rb') as fp:
            response = self.client.post("{}upload/".format(dataset_url), {'attachment': fp})
            self.assertContains(response, '"success":true',
                                status_code=status.HTTP_201_CREATED)

        response = self.client.get(dataset_url)
        self.assertContains(response, '{}archive/'.format(dataset_url),
                            status_code=status.HTTP_200_OK)

        response = self.client.get('{}archive/'.format(dataset_url))
        self.assertContains(response, '')
        self.assertTrue("X-Sendfile" in response)
        self.assertTrue(response["X-Sendfile"].find("archives/NGT0004_1.0_"))
        self.assertTrue("Content-Disposition" in response)
        self.assertEqual("attachment; filename=NGT0003_0.0_Unnamed.zip", response['Content-Disposition'])

    def test_client_get(self):
        # Unauthorized user that is not in any groups
        self.login_user("vibe")
        response = self.client.get('/api/v1/datasets/2/')
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

        self.login_user("auser")
        response = self.client.get('/api/v1/datasets/2/')
        value = json.loads(response.content.decode('utf-8'))
        self.assertEqual(value,
                         {'modified_date': '2016-10-28T23:01:20.066913Z', 'doi': '', 'start_date': '2016-10-28',
                          'status_comment': '', 'plots': ['http://testserver/api/v1/plots/1/'],
                          'created_date': '2016-10-28T19:15:35.013361Z',
                          'funding_organizations': 'A few funding organizations',
                          'authors': ['http://testserver/api/v1/people/2/'], 'cdiac_import': False,
                          'doe_funding_contract_numbers': '',
                          'description': 'Qui illud verear persequeris te. Vis probo nihil verear an, zril tamquam philosophia eos te, quo ne fugit movet contentiones. Quas mucius detraxit vis an, vero omnesque petentium sit ea. Id ius inimicus comprehensam.',
                          'submission_date': '2016-10-28', 'qaqc_method_description': '',
                          'variables': ['http://testserver/api/v1/variables/1/',
                                        'http://testserver/api/v1/variables/2/',
                                        'http://testserver/api/v1/variables/3/'], 'archive': None,
                          'cdiac_submission_contact': None, 'reference': '', 'additional_access_information': '',
                          'contact': 'http://testserver/api/v1/people/2/', 'acknowledgement': '',
                          'data_set_id': 'NGT0001',
                          'modified_by': 'auser', 'status': '1', 'ngee_tropics_resources': True, 'qaqc_status': None,
                          'end_date': None, 'additional_reference_information': '', 'name': 'Data Set 2',
                          'created_by': 'auser', 'sites': ['http://testserver/api/v1/sites/1/'],
                          'originating_institution': None, 'version': '0.0',
                          'url': 'http://testserver/api/v1/datasets/2/', 'access_level': '0'}

                         )
        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_client_post(self):
        self.login_user("auser")
        response = self.client.post('/api/v1/datasets/',
                                    data='{"name":"FooBarBaz","description":"A FooBarBaz DataSet",'
                                         '"authors":["http://testserver/api/v1/people/2/"] }',
                                    content_type='application/json')
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        # Was the notification email sent?
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]

        self.assertEqual(email.subject,"[ngt-archive-test] Dataset Draft (NGT0003)")
        self.assertTrue(email.body.find("The dataset NGT0003:FooBarBaz has been saved as a draft in the "
                                        "NGEE Tropics Archive. The dataset can be "
                                        "viewed at http://testserver.") > 0)
        self.assertEqual(email.to,['myuser@foo.bar'])
        self.assertEqual(email.reply_to, ['ngeet-team@testserver'])

        value = json.loads(response.content.decode('utf-8'))
        self.assertEqual(value['access_level'], '0')
        self.assertEqual(value['sites'], [])
        self.assertEqual(value['created_by'], 'auser')
        self.assertEqual(value['end_date'], None)
        self.assertEqual(value['doe_funding_contract_numbers'], None)
        self.assertEqual(value['funding_organizations'], None)
        self.assertEqual(value['description'], 'A FooBarBaz DataSet')
        self.assertEqual(value['additional_access_information'], None)
        self.assertEqual(value['name'], 'FooBarBaz')
        self.assertEqual(value['modified_by'], 'auser')
        self.assertEqual(value['ngee_tropics_resources'], False)
        self.assertEqual(value['status'], '0')
        self.assertEqual(value['doi'], None)
        self.assertEqual(value['plots'], [])
        self.assertEqual(value['contact'], None)
        self.assertEqual(value['reference'], None)
        self.assertEqual(value['variables'], [])
        self.assertEqual(value['additional_reference_information'], None)
        self.assertEqual(value['start_date'], None)
        self.assertEqual(value['acknowledgement'], None)
        self.assertEqual(value['status_comment'], None)
        self.assertEqual(value['submission_date'], None)
        self.assertEqual(value['qaqc_status'], None)
        self.assertEqual(value['authors'], ["http://testserver/api/v1/people/2/"])
        self.assertEqual(value['url'], 'http://testserver/api/v1/datasets/4/')
        self.assertEqual(value['qaqc_method_description'], None)

        # The submit action should fail
        response = self.client.post('/api/v1/datasets/4/submit/')
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

        value = json.loads(response.content.decode('utf-8'))
        self.assertEqual({'missingRequiredFields': ['sites',
                                                    'contact',
                                                    'variables',
                                                    'funding_organizations',
                                                    'originating_institution']}, value)

    def test_client_put(self):
        self.login_user("auser")
        response = self.client.put('/api/v1/datasets/1/',
                                   data='{"data_set_id":"FooBarBaz","description":"A FooBarBaz DataSet",'
                                        '"name": "Data Set 1", '
                                        '"status_comment": "",'
                                        '"doi": "",'
                                        '"start_date": "2016-10-28",'
                                        '"end_date": null,'
                                        '"qaqc_status": null,'
                                        '"qaqc_method_description": "",'
                                        '"ngee_tropics_resources": true,'
                                        '"funding_organizations": "",'
                                        '"doe_funding_contract_numbers": "",'
                                        '"acknowledgement": "",'
                                        '"reference": "",'
                                        '"additional_reference_information": "",'
                                        '"additional_access_information": "",'
                                        '"submission_date": "2016-10-28T19:12:35Z",'
                                        '"contact": "http://testserver/api/v1/people/4/",'
                                        '"authors": ["http://testserver/api/v1/people/1/"],'
                                        '"sites": ["http://testserver/api/v1/sites/1/"],'
                                        '"plots": ["http://testserver/api/v1/plots/1/"],'
                                        '"variables": ["http://testserver/api/v1/variables/1/", '
                                        '"http://testserver/api/v1/variables/2/"]}',
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
        self.assertEqual({'detail': 'Only a data set in DRAFT status may be submitted'}, value)

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
        self.assertEqual({'missingRequiredFields': ['authors', 'funding_organizations', 'originating_institution']},
                         value)

        response = self.client.put('/api/v1/datasets/1/',
                                   data='{"data_set_id":"FooBarBaz","description":"A FooBarBaz DataSet",'
                                        '"name": "Data Set 1", '
                                        '"status_comment": "",'
                                        '"doi": "",'
                                        '"start_date": "2016-10-28",'
                                        '"end_date": null,'
                                        '"qaqc_status": null,'
                                        '"qaqc_method_description": "",'
                                        '"ngee_tropics_resources": true,'
                                        '"funding_organizations": "The funding organizations for my dataset",'
                                        '"doe_funding_contract_numbers": "",'
                                        '"acknowledgement": "",'
                                        '"reference": "",'
                                        '"additional_reference_information": "",'
                                        '"originating_institution": "Lawrence Berkeley National Lab",'
                                        '"additional_access_information": "",'
                                        '"submission_date": "2016-10-28T19:12:35Z",'
                                        '"contact": "http://testserver/api/v1/people/4/",'
                                        '"authors": ["http://testserver/api/v1/people/1/"],'
                                        '"sites": ["http://testserver/api/v1/sites/1/"],'
                                        '"plots": ["http://testserver/api/v1/plots/1/"],'
                                        '"variables": ["http://testserver/api/v1/variables/1/", '
                                        '"http://testserver/api/v1/variables/2/"]}',
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
        # NGT Administrator may edit any DRAFT status (this will fail due to missing fields)
        response = self.client.get("/api/v1/datasets/1/submit/")  # In draft mode, owned by auser
        value = json.loads(response.content.decode('utf-8'))
        self.assertEqual({'missingRequiredFields': ['authors', 'funding_organizations', 'originating_institution']},
                         value)
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

        self.assertEqual(0, len(mail.outbox))  # no notification emails sent

        #########################################################################
        # Cannot submit a dataset that it already in SUBMITTED status
        response = self.client.get("/api/v1/datasets/2/submit/")  # In submitted mode, owned by auser
        value = json.loads(response.content.decode('utf-8'))
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertEqual({'detail': 'Only a data set in DRAFT status may be submitted'}, value)
        self.assertEqual(0, len(mail.outbox))  # no notification emails sent

        #########################################################################
        # NGT Administrator may edit a dataset in SUBMITTED status
        response = self.client.put('/api/v1/datasets/2/',
                                   data='{"description":"A FooBarBaz DataSet",'
                                        '"name": "Data Set 2", '
                                        '"status_comment": "",'
                                        '"doi": "",'
                                        '"originating_institution": "Lawrence Berkeley National Lab",'
                                        '"start_date": "2016-10-28",'
                                        '"end_date": null,'
                                        '"qaqc_status": null,'
                                        '"qaqc_method_description": "",'
                                        '"ngee_tropics_resources": true,'
                                        '"funding_organizations": "The funding organizations for my dataset",'
                                        '"doe_funding_contract_numbers": "",'
                                        '"acknowledgement": "",'
                                        '"reference": "",'
                                        '"access_level": "0",'
                                        '"additional_reference_information": "",'
                                        '"additional_access_information": "",'
                                        '"submission_date": "2016-10-28T19:12:35Z",'
                                        '"contact": "http://testserver/api/v1/people/4/",'
                                        '"authors": ["http://testserver/api/v1/people/4/","http://testserver/api/v1/people/3/"],'
                                        '"sites": ["http://testserver/api/v1/sites/1/"],'
                                        '"plots": ["http://testserver/api/v1/plots/1/"],'
                                        '"variables": ["http://testserver/api/v1/variables/1/", '
                                        '"http://testserver/api/v1/variables/2/"]}',
                                   content_type='application/json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        response = self.client.get("/api/v1/datasets/2/")  # check authors
        value = json.loads(response.content.decode('utf-8'))
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(value["description"], "A FooBarBaz DataSet")
        self.assertEqual(value["name"], "Data Set 2")
        self.assertEqual(value["status_comment"], "")
        self.assertEqual(value["doi"], "")
        self.assertEqual(value["originating_institution"], "Lawrence Berkeley National Lab")
        self.assertEqual(value["start_date"], "2016-10-28")
        self.assertEqual(value["end_date"], None)
        self.assertEqual(value["qaqc_status"], None)
        self.assertEqual(value["qaqc_method_description"], "")
        self.assertEqual(value["ngee_tropics_resources"], True)
        self.assertEqual(value["funding_organizations"], "The funding organizations for my dataset")
        self.assertEqual(value["doe_funding_contract_numbers"], "")
        self.assertEqual(value["acknowledgement"], "")
        self.assertEqual(value["reference"], "")
        self.assertEqual(value["access_level"], "0")
        self.assertEqual(value["additional_reference_information"], "")
        self.assertEqual(value["additional_access_information"], "")
        self.assertEqual(value["contact"], "http://testserver/api/v1/people/4/")
        self.assertEqual(value["authors"], ["http://testserver/api/v1/people/4/", "http://testserver/api/v1/people/3/"])
        self.assertEqual(value["sites"], ["http://testserver/api/v1/sites/1/"])
        self.assertEqual(value["plots"], ["http://testserver/api/v1/plots/1/"])
        self.assertEqual(value["variables"],
                         ["http://testserver/api/v1/variables/1/", "http://testserver/api/v1/variables/2/"])

        #########################################################################
        # A dataset that is not in SUBMITTED status may not be approved
        response = self.client.get("/api/v1/datasets/1/approve/")  # In draft mode, owned by auser
        value = json.loads(response.content.decode('utf-8'))
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertEqual({'detail': 'Only a data set in SUBMITTED status may be approved'}, value)
        self.assertEqual(0, len(mail.outbox))  # no notification emails sent

        #########################################################################
        # NGT Administrator my APPROVE a SUBMITTED dataset
        response = self.client.get("/api/v1/datasets/2/approve/")  # In submitted mode, owned by auser
        value = json.loads(response.content.decode('utf-8'))
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual({'detail': 'DataSet has been approved.', 'success': True}, value)

        # Was the notification email sent?
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]

        self.assertEqual(email.subject, "[ngt-archive-test] Dataset Approved (NGT0001)")
        self.assertTrue(email.body.find("The dataset NGT0001:Data Set 2  created on 10/28/2016 "
                                        "has been approved for release. The dataset can be viewed at http://testserver.") > 0)
        self.assertEqual(email.to, ['myuser@foo.bar'])
        self.assertEqual(email.reply_to, ['ngeet-team@testserver'])

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
        self.assertEqual({'detail': 'Only a data set in SUBMITTED status may be un-submitted'}, value)

        # Make sure no additional notification was sent
        self.assertEqual(len(mail.outbox), 1)


        response = self.client.get("/api/v1/datasets/2/unapprove/")  # In approved mode, owned by auser
        value = json.loads(response.content.decode('utf-8'))
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual({'detail': 'DataSet has been unapproved.', 'success': True}, value)
        self.assertEqual(1, len(mail.outbox))  # no notification emails sent

        #########################################################################
        # NGT Administrator my unapproved a dataset (put back into submitted mode)
        response = self.client.get("/api/v1/datasets/1/unapprove/")  # In approved mode, owned by auser
        value = json.loads(response.content.decode('utf-8'))
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertEqual({'detail': 'Only a data set in APPROVED status may be unapproved'}, value)
        response = self.client.get("/api/v1/datasets/2/")  # Check the status
        value = json.loads(response.content.decode('utf-8'))
        self.assertEqual(value['status'], '1')
        self.assertEqual(1, len(mail.outbox))  # no notification emails sent

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

    def test_user_delete_not_allowed(self):
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
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

        response = self.client.get("/api/v1/datasets/1/")  # should be deleted
        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_admin_delete_not_allowed(self):
        """
        Test Admin delete
        :return:
        """
        self.login_user("admin")

        #########################################################################
        # NGT User may  delete a SUBMITTED dataset
        response = self.client.delete("/api/v1/datasets/2/")  # In submitted mode, owned by auser
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

        response = self.client.get("/api/v1/datasets/2/")  # should be deleted
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        #########################################################################
        # NGT User may delete a DRAFT dataset
        response = self.client.delete("/api/v1/datasets/1/")  # In submitted mode, owned by auser
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

        response = self.client.get("/api/v1/datasets/1/")  # should be deleted
        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_upload(self):
        """
        Test Dataset Archive Upload
        :return:
        """
        self.login_user("admin")
        with open('{}/Archive.zip'.format(dirname(__file__)), 'rb') as fp:
            response = self.client.post('/api/v1/datasets/1/upload/', {'attachment': fp})
            self.assertContains(response, '"success":true',
                                status_code=status.HTTP_201_CREATED)

        response = self.client.get('/api/v1/datasets/1/')
        self.assertContains(response, 'http://testserver/api/v1/datasets/1/archive/',
                            status_code=status.HTTP_200_OK)

        response = self.client.get('/api/v1/datasets/1/archive/')
        self.assertContains(response, '')
        self.assertTrue("X-Sendfile" in response)
        self.assertTrue(response["X-Sendfile"].find("archives/NGT1_1.0_"))
        self.assertTrue("Content-Disposition" in response)
        self.assertEqual("attachment; filename=NGT0000_0.0_Data_Set_1.zip", response['Content-Disposition'])

        downloadlog = DataSetDownloadLog.objects.all()
        self.assertEqual(len(downloadlog),1)


        # Now try to upload and invalid file
        with open('{}/invalid_upload.txt'.format(dirname(__file__)), 'r') as fp:
            response = self.client.post('/api/v1/datasets/1/upload/', {'attachment': fp})
            self.assertContains(response, '"success":false',
                                status_code=status.HTTP_400_BAD_REQUEST)
            self.assertContains(response, 'Filetype text/plain not supported. Allowed types: application/zip, ',
                                status_code=status.HTTP_400_BAD_REQUEST)

        response = self.client.get('/api/v1/datasets/1/')
        self.assertContains(response, 'http://testserver/api/v1/datasets/1/archive/',
                            status_code=status.HTTP_200_OK)

        response = self.client.get('/api/v1/datasets/1/archive/')
        self.assertContains(response, '')
        self.assertTrue("X-Sendfile" in response)
        self.assertTrue(response["X-Sendfile"].find("archives/0000/0000/NGT0000/0.0/NGT0000_0.0") > -1)
        self.assertTrue("Content-Disposition" in response)
        self.assertEqual("attachment; filename=NGT0000_0.0_Data_Set_1.zip", response['Content-Disposition'])

        response = self.client.put('/api/v1/datasets/1/',
                                   data='{"data_set_id":"FooBarBaz","description":"A FooBarBaz DataSet",'
                                        '"name": "Data Set 1", '
                                        '"status_comment": "",'
                                        '"doi": "",'
                                        '"start_date": "2016-10-28",'
                                        '"end_date": null,'
                                        '"qaqc_status": null,'
                                        '"qaqc_method_description": "",'
                                        '"ngee_tropics_resources": true,'
                                        '"funding_organizations": "The funding organizations for my dataset",'
                                        '"doe_funding_contract_numbers": "",'
                                        '"acknowledgement": "",'
                                        '"reference": "",'
                                        '"additional_reference_information": "",'
                                        '"originating_institution": "Lawrence Berkeley National Lab",'
                                        '"additional_access_information": "",'
                                        '"submission_date": "2016-10-28T19:12:35Z",'
                                        '"contact": "http://testserver/api/v1/people/4/",'
                                        '"authors": ["http://testserver/api/v1/people/1/"],'
                                        '"sites": ["http://testserver/api/v1/sites/1/"],'
                                        '"plots": ["http://testserver/api/v1/plots/1/"],'
                                        '"variables": ["http://testserver/api/v1/variables/1/", '
                                        '"http://testserver/api/v1/variables/2/"]}',
                                   content_type='application/json')

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        #########################################################################
        # NGT User may not SUBMIT a dataset in DRAFT mode if they owne it
        outbox_len = len(mail.outbox)
        response = self.client.get("/api/v1/datasets/1/submit/")  # In draft mode, owned by auser
        value = json.loads(response.content.decode('utf-8'))
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual({'detail': 'DataSet has been submitted.', 'success': True}, value)
        self.assertEqual(outbox_len + 1, len(mail.outbox))  # notification emails sent
        email = mail.outbox[0]
        self.assertEqual(email.subject, "[ngt-archive-test] Dataset Submitted (NGT0000)")
        self.assertTrue(email.body.find("The dataset NGT0000:Data Set 1 created on 10/28/2016 was "
                                        "submitted to the NGEE Tropics Archive. The dataset can be "
                                        "viewed at http://testserver.") > 0)
        self.assertEqual(email.to, ['myuser@foo.bar'])

        response = self.client.get("/api/v1/datasets/1/")
        self.assertContains(response, '"version":"1.0"')

        response = self.client.get('/api/v1/datasets/1/archive/')
        self.assertContains(response, '')
        self.assertTrue("X-Sendfile" in response)
        self.assertTrue(response["X-Sendfile"].find("archives/0000/0000/NGT0000/1.0/NGT0000_1.0") > -1)
        self.assertTrue("Content-Disposition" in response)
        self.assertEqual("attachment; filename=NGT0000_1.0_Data_Set_1.zip", response['Content-Disposition'])

        import os
        shutil.rmtree(os.path.join(settings.ARCHIVE_API['DATASET_ARCHIVE_ROOT'], "0000"))

    def test_upload_not_found(self):
        """
        Test Dataset Archive Upload
        :return:
        """
        self.login_user("auser")  # auser does not own Dataset 3
        with open('{}/invalid_upload.txt'.format(dirname(__file__)), 'r') as fp:
            response = self.client.post('/api/v1/datasets/3/upload/', {'attachment': fp})
            self.assertContains(response, '"detail":"Not found."',
                                status_code=status.HTTP_404_NOT_FOUND)

        response = self.client.get('/api/v1/datasets/3/')
        self.assertNotContains(response, 'http://testserver/api/v1/datasets/3/archive/',
                               status_code=status.HTTP_404_NOT_FOUND)

        response = self.client.get('http://testserver/api/v1/datasets/3/archive/')
        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)

    def test_upload_permission_denied(self):
        """
        Test Dataset Archive Upload
        :return:
        """
        self.login_user("auser")  # auser does not own Dataset 3
        with open('{}/invalid_upload.txt'.format(dirname(__file__)), 'r') as fp:
            response = self.client.post('/api/v1/datasets/2/upload/', {'attachment': fp})
            self.assertContains(response, '"detail":"You do not have permission to perform this action."',
                                status_code=status.HTTP_403_FORBIDDEN)

        response = self.client.get('/api/v1/datasets/2/')
        self.assertNotContains(response, 'http://testserver/api/v1/datasets/2/archive/',
                               status_code=status.HTTP_200_OK)

        response = self.client.get('http://testserver/api/v1/datasets/2/archive/')
        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)

    def test_upload_invalid(self):
        """
        Test Dataset Archive Upload
        :return:
        """
        self.login_user("admin")
        with open('{}/invalid_upload.txt'.format(dirname(__file__)), 'r') as fp:
            response = self.client.post('/api/v1/datasets/1/upload/', {'attachment': fp})
            self.assertContains(response, '"success":false',
                                status_code=status.HTTP_400_BAD_REQUEST)
            self.assertContains(response, 'Filetype text/plain not supported. Allowed types: application/zip',
                                status_code=status.HTTP_400_BAD_REQUEST)

        response = self.client.get('/api/v1/datasets/1/')
        self.assertNotContains(response, 'http://testserver/api/v1/datasets/1/archive/',
                               status_code=status.HTTP_200_OK)

        response = self.client.get('http://testserver/api/v1/datasets/1/archive/')
        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)

    def test_issue_118(self):
        """Error when trying to submit a dataset with ngee_tropics_resources set to false #118"""
        self.login_user("auser")
        response = self.client.put('/api/v1/datasets/1/',
                                   data='{"data_set_id":"FooBarBaz","description":"A FooBarBaz DataSet",'
                                        '"name": "Data Set 1", '
                                        '"status_comment": "",'
                                        '"doi": "",'
                                        '"start_date": "2016-10-28",'
                                        '"end_date": null,'
                                        '"qaqc_status": null,'
                                        '"qaqc_method_description": "",'
                                        '"ngee_tropics_resources": false,'
                                        '"funding_organizations": "The funding organizations for my dataset",'
                                        '"doe_funding_contract_numbers": "",'
                                        '"acknowledgement": "",'
                                        '"reference": "",'
                                        '"additional_reference_information": "",'
                                        '"originating_institution": "Lawrence Berkeley National Lab",'
                                        '"additional_access_information": "",'
                                        '"submission_date": "2016-10-28T19:12:35Z",'
                                        '"contact": "http://testserver/api/v1/people/4/",'
                                        '"authors": ["http://testserver/api/v1/people/1/"],'
                                        '"sites": ["http://testserver/api/v1/sites/1/"],'
                                        '"plots": ["http://testserver/api/v1/plots/1/"],'
                                        '"variables": ["http://testserver/api/v1/variables/1/", '
                                        '"http://testserver/api/v1/variables/2/"]}',
                                   content_type='application/json')

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        #########################################################################
        # NGT User may not SUBMIT a dataset in DRAFT mode if they owne it
        response = self.client.get("/api/v1/datasets/1/submit/")  # In draft mode, owned by auser
        value = json.loads(response.content.decode('utf-8'))
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual({'detail': 'DataSet has been submitted.', 'success': True}, value)

    def test_issue_74(self):
        self.login_user("auser")
        response = self.client.post('/api/v1/datasets/',
                                    data='{"description":"A FooBarBaz DataSet",'
                                         '"authors":["http://testserver/api/v1/people/2/"],'
                                         '"sites":["http://testserver/api/v1/sites/1/"] ,'
                                         '"plots":["http://testserver/api/v1/plots/1/"],'
                                         '"variables":["http://testserver/api/v1/variables/1/"]  }',
                                    content_type='application/json')
        self.assertTrue(status.HTTP_201_CREATED, response.status_code)
        dataset_url = json.loads(response.content.decode('utf-8'))["url"]

        response = self.client.get(dataset_url)

        self.assertContains(response,
                            "http://testserver/api/v1/variables/1/")
        self.assertContains(response,
                            "http://testserver/api/v1/sites/1/")
        self.assertContains(response,
                            "http://testserver/api/v1/plots/1/")


    @mock.patch('django.core.files.uploadedfile.InMemoryUploadedFile.size', new_callable=PropertyMock)
    def test_issue_117(self, mock_file_size):
        """Is the backend enforcing a file size limit? Testing limits for admin and regular users"""
        mock_file_size.return_value = 2147483648
        self.login_user("auser")
        with open('{}/Archive.zip'.format(dirname(__file__)), 'rb') as fp:
            response = self.client.post('/api/v1/datasets/1/upload/', {'attachment': fp})
            self.assertContains(response, '"success":false',
                                status_code=status.HTTP_400_BAD_REQUEST)
            self.assertContains(response,"Uploaded file size is 2048.0 MB. Max upload size is 1024.0 MB",
                                status_code=status.HTTP_400_BAD_REQUEST)

        mock_file_size.return_value = 3147483648
        self.login_user("admin")
        with open('{}/Archive.zip'.format(dirname(__file__)), 'rb') as fp:
            response = self.client.post('/api/v1/datasets/1/upload/', {'attachment': fp})
            self.assertContains(response, '"success":false',
                                status_code=status.HTTP_400_BAD_REQUEST)
            self.assertContains(response, "Uploaded file size is 3001.7 MB. Max upload size is 2048.0 MB",
                                status_code=status.HTTP_400_BAD_REQUEST)

class SiteClientTestCase(APITestCase):
    fixtures = ('test_auth.json', 'test_archive_api.json',)

    def login_user(self, username):
        user = User.objects.get(username=username)
        self.client.force_login(user)

    def setUp(self):
        self.client = Client()
        user = User.objects.get(username="auser")
        self.client.force_login(user)

    def test_client_list(self):
        # Unauthorized user that is not in any groups
        self.login_user("vibe")
        response = self.client.get('/api/v1/sites/')
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

        self.login_user("auser")
        response = self.client.get('/api/v1/sites/')
        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_client_get(self):
        # Unauthorized user that is not in any groups
        self.login_user("vibe")
        response = self.client.get('/api/v1/sites/1/')
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

        self.login_user("auser")
        response = self.client.get('/api/v1/sites/1/')
        self.assertEqual(json.loads(response.content.decode('utf-8')),
                         {"url": "http://testserver/api/v1/sites/1/", "site_id": "CC-CCPD",
                          "name": "Central City CCPD",
                          "description": "Et doming epicurei posidonium has, an sit sanctus intellegebat. Ne malis reprehendunt mea. Iisque dolorem vel cu. Ut nam sapientem appellantur definitiones, copiosae placerat inimicus per ei. Cu pro reque putant, cu perfecto urbanitas posidonium eum, pri probo laoreet cu. Ei duo cetero concludaturque, ei adhuc facilis sit.\r\n\r\nAn aeque harum ius, mea ut erant verear salutandi. Eligendi recusabo usu ad. Ad modo vero consequat his, ne aperiam alienum suscipiantur his. Altera laoreet petentium pro ut. His option vocibus at. Vix no semper omnesque maluisset, accusata qualisque ut pro. Eos sint constituto temporibus in.",
                          "country": "United States", "state_province": "", "utc_offset": -9,
                          "location_latitude": -8.983987234, "location_longitude": 5.9832932847,
                          "location_elevation": "100-400", "location_map_url": "",
                          "location_bounding_box_ul_latitude": None,
                          "location_bounding_box_ul_longitude": None, "location_bounding_box_lr_latitude": None,
                          "location_bounding_box_lr_longitude": None, "site_urls": "http://centralcityccpd.baz",
                          "submission_date": "2016-10-01", "contacts": [], "pis": [],
                          "submission": "http://testserver/api/v1/people/3/"})
        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_client_post(self):
        response = self.client.post('/api/v1/sites/',
                                    data='{"data_set_id":"FooBarBaz","description":"A FooBarBaz DataSet"}',
                                    content_type='application/json')
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_client_put(self):
        response = self.client.put('/api/v1/sites/2/',
                                   data='{"data_set_id":"FooBarBaz","description":"A FooBarBaz DataSet"}',
                                   content_type='application/json')
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)


class PlotClientTestCase(APITestCase):
    fixtures = ('test_auth.json', 'test_archive_api.json',)

    def login_user(self, username):
        user = User.objects.get(username=username)
        self.client.force_login(user)

    def setUp(self):
        self.client = Client()
        self.login_user("auser")


    def test_client_list(self):
        # Unauthorized user that is not in any groups
        self.login_user("vibe")
        response = self.client.get('/api/v1/plots/')
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

        self.login_user("auser")
        response = self.client.get('/api/v1/plots/')
        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_client_get(self):
        # Unauthorized user that is not in any groups
        self.login_user("vibe")
        response = self.client.get('/api/v1/sites/1/')
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

        self.login_user("auser")
        response = self.client.get('/api/v1/plots/1/')
        self.assertEqual(json.loads(response.content.decode('utf-8')),
                         {"url": "http://testserver/api/v1/plots/1/", "plot_id": "CC-CCPD1",
                          "name": "Central City CCPD Plot 1",
                          "description": "Sed ut perspiciatis, unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam eaque ipsa, quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt, explicabo. Nemo enim ipsam voluptatem, quia voluptas sit, aspernatur aut odit aut fugit, sed quia consequuntur magni dolores eos, qui ratione voluptatem sequi nesciunt, neque porro quisquam est, qui dolorem ipsum, quia dolor sit amet, consectetur, adipisci[ng] velit, sed quia non numquam [do] eius modi tempora inci[di]dunt, ut labore et dolore magnam aliquam quaerat voluptatem. Ut enim ad minima veniam, quis nostrum exercitationem ullam corporis suscipit laboriosam, nisi ut aliquid ex ea commodi consequatur? Quis autem vel eum iure reprehenderit, qui in ea voluptate velit esse, quam nihil molestiae consequatur, vel illum, qui dolorem eum fugiat, quo voluptas nulla pariatur",
                          "size": "", "location_elevation": "", "location_kmz_url": "", "submission_date": "2016-10-08",
                          "pi": "http://testserver/api/v1/people/3/",
                          "site": "http://testserver/api/v1/sites/1/",
                          "submission": "http://testserver/api/v1/people/4/"})
        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_client_post(self):
        response = self.client.post('/api/v1/plots/',
                                    data='{"data_set_id":"FooBarBaz","description":"A FooBarBaz DataSet"}',
                                    content_type='application/json')
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_client_put(self):
        response = self.client.put('/api/v1/plots/1/',
                                   data='{"data_set_id":"FooBarBaz","description":"A FooBarBaz DataSet"}',
                                   content_type='application/json')
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)


class ContactClientTestCase(APITestCase):
    fixtures = ('test_auth.json', 'test_archive_api.json',)

    def login_user(self, username):
        user = User.objects.get(username=username)
        self.client.force_login(user)

    def setUp(self):
        self.client = Client()
        self.login_user("auser")

    def test_client_list(self):
        # Unauthorized user that is not in any groups
        self.login_user("vibe")
        response = self.client.get('/api/v1/people/')
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

        self.login_user("auser")
        response = self.client.get('/api/v1/people/?format=api')
        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_client_get(self):
        # Unauthorized user that is not in any groups
        self.login_user("vibe")
        response = self.client.get('/api/v1/people/2/')
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

        self.login_user("auser")
        response = self.client.get('/api/v1/people/2/')
        self.assertEqual(json.loads(response.content.decode('utf-8')),
                         {"url": "http://testserver/api/v1/people/2/", "first_name": "Luke",
                          "last_name": "Cage", "email": "lcage@foobar.baz", "institution_affiliation": "POWER"})
        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_client_post(self):
        response = self.client.post('/api/v1/people/',
                                    data='{"first_name":"Killer","last_name":"Frost","email":"kfrost@earth2.baz","institution_affiliation":"ZOOM"}',
                                    content_type='application/json')
        self.assertEqual(json.loads(response.content.decode('utf-8')),
                         {"url": "http://testserver/api/v1/people/6/", "first_name": "Killer", "last_name": "Frost",
                          "email": "kfrost@earth2.baz", "institution_affiliation": "ZOOM"})
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

    def test_client_put(self):
        response = self.client.put('/api/v1/people/2/',
                                   data='{"url": "http://testserver/api/v1/people/2/", "first_name": "Luke", "last_name": "Cage", "email": "lcage@foobar.baz", "institution_affiliation": "POW"}',
                                   content_type='application/json')
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)


class VariableClientTestCase(APITestCase):
    fixtures = ('test_auth.json', 'test_archive_api.json',)

    def login_user(self, username):
        user = User.objects.get(username=username)
        self.client.force_login(user)

    def setUp(self):
        self.client = Client()
        user = User.objects.get(username="auser")
        self.client.force_login(user)

    def test_client_list(self):
        # Unauthorized user that is not in any groups
        self.login_user("vibe")
        response = self.client.get('/api/v1/variables/')
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

        self.login_user("auser")
        response = self.client.get('/api/v1/variables/')
        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_client_get(self):
        # Unauthorized user that is not in any groups
        self.login_user("vibe")
        response = self.client.get('/api/v1/variables/2/')
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

        self.login_user("auser")
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
