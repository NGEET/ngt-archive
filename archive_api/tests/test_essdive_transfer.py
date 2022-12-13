from archive_api.service.essdive_transfer.tasks import requests

import json

import os

from django.core.management import call_command
import pytest
from celery.contrib.testing.app import TestApp
from celery.contrib.testing.worker import start_worker

import archive_api
from archive_api.service.essdive_transfer import tasks, crosswalk

BASE_PATH = os.path.dirname(__file__)

# ESS-DIVE Transfers in different states
RUN_ID_START = 1
RUN_ID_START_PREVIOUS = 5
RUN_ID_TRANSFER = 2
RUN_ID_END = 3

# Datasets in different states
DATASET_DRAFT = 1
DATASET_APPROVED = 5
DATASET_PREVIOUS = 4


def create_mock_request(json_file, status_code=200):
    """
    Create the Mock request function with the specified JSON file is the response body

    :param json_file:
    :return:
    """

    filename = os.path.join(BASE_PATH, json_file)
    file_name = os.path.join(filename)

    with open(file_name, 'r') as f:
        file_json = json.load(f)

    def mock_request(*args, **kwargs):
        """ Returns a mock of the get request in archive_api.essdive_transfer.tasks"""

        class DummyResponse(object):

            @property
            def status_code(self):
                return status_code

            def json(*args, **kwargs):
                return file_json

        return DummyResponse()

    return mock_request


def mock_get_request(*args, **kwargs):
    """ Returns a mock of the get request in archive_api.essdive_transfer.tasks.search"""

    # Determine which call is being made search or get
    filename = "ngt_essdive_dataset_result.json"
    if args[0].endswith("ess-dive-e1902f9728f70db-20220430T030400919221"):
        filename = "ngt_essdive_dataset.json"

    class DummyResponse(object):

        @property
        def status_code(self):
            return 200

        def json(*args, **kwargs):
            file_name = os.path.join(BASE_PATH, filename)

            with open(file_name, 'r') as f:
                return json.load(f)

    return DummyResponse()


def mock_get_request_unauthorized(*args, **kwargs):
    """ Returns a mock of the get request in archive_api.essdive_transfer.tasks.search"""

    # Determine which call is being made search or get
    filename = "ngt_essdive_dataset_unauthorized.json"

    class DummyResponse(object):

        @property
        def status_code(self):
            return 401

        def json(*args, **kwargs):
            file_name = os.path.join(BASE_PATH, filename)

            with open(file_name, 'r') as f:
                return json.load(f)

    return DummyResponse()


@pytest.fixture
def celery_setup(settings, django_db_blocker, monkeypatch):
    """Sets up celery environment for testing and loads some data"""

    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_EAGER_PROPAGATES = True
    settings.CELERY_TASK_STORE_EAGER_RESULT = True

    with django_db_blocker.unblock():
        call_command('loaddata', 'test_auth.json')
        call_command('loaddata', 'test_archive_api.json')
        call_command('loaddata', 'test_essdive_transfer.json')

    TestApp()
    from ngt_archive.celery_app import app
    return start_worker(app)


@pytest.mark.django_db(transaction=True)
def test_workflow_execution_success(celery_setup, settings, monkeypatch):
    """Test the Django post_save signal that runs the workflow that succeeds"""

    monkeypatch.setattr(requests, "get", mock_get_request)
    monkeypatch.setattr(requests, "request", create_mock_request("ngt_essdive_dataset.json"))

    from archive_api.models import EssDiveTransfer, DataSet

    assert settings.CELERY_TASK_ALWAYS_EAGER is True
    assert settings.CELERY_EAGER_PROPAGATES is True

    dataset = DataSet.objects.all().get(id=DATASET_DRAFT)
    obj = EssDiveTransfer.objects.create(dataset=dataset, type=EssDiveTransfer.TYPE_METADATA)

    transfer_job = EssDiveTransfer.objects.all().get(id=obj.id)

    assert transfer_job is not None
    assert transfer_job.status == EssDiveTransfer.STATUS_SUCCESS
    assert transfer_job.start_time is not None
    assert transfer_job.end_time is not None


@pytest.mark.django_db()
def test_transfer_start_no_previous(celery_setup, monkeypatch):
    """Test start task"""

    monkeypatch.setattr(requests, "get", mock_get_request)

    task = tasks.transfer_start.delay(RUN_ID_START)
    results = task.get()
    assert results == {'essdive_id': 'ess-dive-e1902f9728f70db-20220430T030400919221',
                       'ngt_id': 'NGT0000',
                       'run_id': RUN_ID_START}


@pytest.mark.django_db()
def test_transfer_start_has_previous(celery_setup, monkeypatch):
    """Test start task"""

    monkeypatch.setattr(requests, "get", mock_get_request)

    task = tasks.transfer_start.delay(RUN_ID_START_PREVIOUS)
    results = task.get()
    assert results == {'essdive_id': 'ess-dive-6a065b8db64b880-20220503T150116078267',
                       'ngt_id': 'NGT0003',
                       'run_id': RUN_ID_START_PREVIOUS}


@pytest.mark.django_db()
def test_transfer_start_has_previous_not_found(celery_setup, monkeypatch):
    """Test start task"""

    monkeypatch.setattr(requests, "get", create_mock_request("ngt_essdive_dataset.json", 404))

    task = tasks.transfer_start.delay(RUN_ID_START_PREVIOUS)
    try:
        task.get()
        pytest.fail("RunError should have been thrown")
    except archive_api.service.essdive_transfer.tasks.RunError as e:
        assert "Invalid ESS-DIVE Transfer 5 - There are one or more previous transfers for " \
               "this dataset but no ESS-DIVE dataset was found." == str(e)


@pytest.mark.django_db()
def test_transfer_start_not_authorized(celery_setup, monkeypatch):
    """Test start task"""

    task = tasks.transfer_start.delay(RUN_ID_START)

    try:
        task.get()
        pytest.fail("RunError should have been thrown")
    except archive_api.service.essdive_transfer.tasks.RunError as e:
        assert "Invalid ESS-DIVE Transfer 1 - You do not have authorized access" == str(e)


@pytest.mark.django_db()
def test_essdive_transfer_task(celery_setup, monkeypatch):
    """Test transfer task"""

    filename = os.path.join(BASE_PATH, "ngt_essdive_dataset.json")
    file_name = os.path.join(filename)

    with open(file_name, 'r') as f:
        file_json = json.load(f)

    monkeypatch.setattr(requests, "request", create_mock_request("ngt_essdive_dataset.json"))

    task = tasks.transfer.delay({'run_id': RUN_ID_TRANSFER, "ngt_id": "NGT0001"})
    results = task.get()
    assert results == {'response': file_json, 'run_id': RUN_ID_TRANSFER, 'status_code': 200}


@pytest.mark.django_db()
def test_essdive_transfer_task_not_authorized(celery_setup, monkeypatch):
    """Test transfer task"""

    task = tasks.transfer.delay({'run_id': RUN_ID_TRANSFER, "ngt_id": "NGT0001"})
    monkeypatch.setattr(requests, "request", create_mock_request("ngt_essdive_dataset_unauthorized.json", 401))

    results = task.get()
    assert results == {'response': {'detail': 'You do not have authorized access'},
                       'run_id': 2,
                       'status_code': 401}


@pytest.mark.django_db()
def test_essdive_task_end(celery_setup):
    """Test start end"""

    task = tasks.transfer_end.delay({'response': {}, 'run_id': RUN_ID_END, 'status_code': 3})
    results = task.get()
    assert results == {'run_id': RUN_ID_END}


@pytest.mark.django_db()
def test_dataset_transform(celery_setup):
    """Test the Dataset to ESS-DIVE JSON-LD Transform"""

    from archive_api.models import DataSet
    dataset = DataSet.objects.all().get(id=DATASET_APPROVED)
    jsonld = crosswalk.dataset_transform(dataset)

    with open(os.path.join(BASE_PATH, "essdive-transfer.jsonld")) as f:
        expected_json = json.load(f)

    assert jsonld == expected_json


@pytest.mark.django_db()
def test_locations_transform(celery_setup):
    """Test the Locations to ESS-DIVE Locations Reporting format Transform"""

    from archive_api.models import DataSet
    dataset = DataSet.objects.all().get(id=DATASET_APPROVED)
    json_locations = crosswalk.locations_transform(dataset)
    print(json_locations)

    with open(os.path.join(BASE_PATH, "essdive_transfer_locations.json")) as f:
        expected_json = json.load(f)

    assert json_locations == expected_json


def test_json_to_csv():
    """Test the JSON to csv writer"""

    with open(os.path.join(BASE_PATH, "essdive_transfer_locations.json")) as f:
        json_to_transform = json.load(f)

    with open(os.path.join(BASE_PATH, "locations.csv")) as f:

        from io import StringIO
        csv_fp = StringIO()
        crosswalk.json_to_csv(csv_fp, json_to_transform)
        assert str(csv_fp.read()).replace("\r", "") == str(f.read()).replace("\r", "")
