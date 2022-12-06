import math

import json

import requests
from celery.app import shared_task
from celery.utils.log import get_task_logger
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import APIException

from archive_api.service.essdive_transfer import crosswalk
from archive_api.models import EssDiveTransfer, ServiceAccount, SERVICE_ACCOUNT_ESSDIVE
from requests_toolbelt.multipart.encoder import MultipartEncoder, MultipartEncoderMonitor

log = get_task_logger(__name__)


class RunError(APIException):
    """
        Error raise when there is a problem with ModelRun
    """

    def __init__(self, run_id, message):
        super(RunError, self).__init__(detail="Invalid ESS-DIVE Transfer {} - {}".format(run_id, message))


@shared_task
def log_error(request, exc, traceback):
    """
    Print task error information to standard error

    :param request:
    :param exc:
    :param traceback:
    :return: None
    """
    log.error('Task Request {} in error "{}" '.format(request.id, exc))


def get(essdive_id):
    """
    Search for the NGEE Tropics dataset on ESS-DIVE
    :param essdive_id: The ESS-DIVE identifier to the dataset
    :return: Response object
    """
    # Get the ESS-DIVE account information
    service_account = ServiceAccount.objects.all().get(service=SERVICE_ACCOUNT_ESSDIVE)

    # Cannot query alternateName field for NGT ID. However can filter by project name and
    #  if the NGT ID is in the text of the metadata.
    response = requests.get(f"{service_account.endpoint}/{essdive_id}",
                            headers={"Authorization": f"Bearer {service_account.secret}"})

    return response


def search(run_id):
    """
    Search for the NGEE Tropics dataset on ESS-DIVE
    :param run_id: The run identifier to the dataset
    :return: Response object
    """
    # Get the ESS-DIVE account information
    service_account = ServiceAccount.objects.all().get(service=SERVICE_ACCOUNT_ESSDIVE)
    # Get the current job for this task
    transfer_job = EssDiveTransfer.objects.all().get(id=run_id)
    # Search for the dataset on ESS-DIVE
    ngt_id = transfer_job.dataset.data_set_id()

    # Cannot query alternateName field for NGT ID. However can filter by project name and
    #  if the NGT ID is in the text of the metadata.
    response = requests.get(f"{service_account.endpoint}?text=*{ngt_id}*&providerName=*NGEE Tropics*",
                            headers={"Authorization": f"Bearer {service_account.secret}"})

    return response


@shared_task
def transfer_start(run_id):
    """
    Prepares the transfer for the specified run_id.

    :param run_id: the run to execute.
    :return:
    """
    log.debug("inputs:{}".format(run_id))

    try:

        # Get the current job for this task
        transfer_job = EssDiveTransfer.objects.all().get(id=run_id)

        response = search(run_id)
        essdive_id = None
        # Does this dataset already exist on ESS-DIVE?
        if response.status_code == status.HTTP_200_OK:

            # Iterate over the results and get the first dataset with the NGT ID in
            # the alternate names. Ignore all other results
            result_json = response.json()
            for d in result_json["result"]:
                essdive_response = get(d["id"])
                essdive_response_json = essdive_response.json()
                log.info(f"Determining if ESS-DIVE dataset ({d['id']}) represents {transfer_job.dataset.data_set_id()}")

                if essdive_response.status_code == status.HTTP_200_OK:
                    # alternateName may be a list or a string
                    if transfer_job.dataset.data_set_id() in essdive_response_json["dataset"]["alternateName"] or \
                            transfer_job.dataset.data_set_id() == essdive_response_json["dataset"]["alternateName"]:
                        essdive_id = d['id']
                        transfer_job.status = EssDiveTransfer.STATUS_QUEUED
                        transfer_job.save()
                        log.info(f"Found ESS-DIVE dataset ({d['id']}) for {transfer_job.dataset.data_set_id()}")
                        break
                else:
                    log.info(f"Ignoring ESS-DIVE dataset ({d['id']}) for {transfer_job.dataset.data_set_id()}")

        elif response.status_code != status.HTTP_404_NOT_FOUND:
            try:
                response_json = response.json()
                transfer_job.response = response_json
                transfer_job.message = response_json["detail"]
            except:
                transfer_job.message = "Problem encounter searching for and existing dataset on ESS-DIVE"

            transfer_job.status = EssDiveTransfer.STATUS_FAILED

            transfer_job.save()
            raise RunError(run_id, transfer_job.message)

        # Return  run information
        return {"run_id": run_id, "essdive_id": essdive_id, 'ngt_id': transfer_job.dataset.data_set_id()}
    except RunError as re:
        raise re
    except Exception as e:
        _raise_run_error(e, run_id)


@shared_task
def transfer(result):
    """
    Executes the ESS-DIVE Transfer.

    Result Args:

        - *run_id*: the transfer job id
        - *essdive_id*: the essdive_id for the transfer
        - *ngt_id*: the ngt_id for the transfer

    :param result:
    :type result: dict
    :return: result
    :rtype: dict
    """
    log.debug("inputs:{}".format(result))

    run_id = result.get("run_id", None)
    essdive_id = result.get("essdive_id", None)
    ngt_id = result.get("ngt_id", None)

    if run_id:

        try:

            # Get the ESS-DIVE account information
            service_account = ServiceAccount.objects.all().get(service=SERVICE_ACCOUNT_ESSDIVE)
            log.info(f"Using {service_account.get_service_display()} service account to transfer data.")
            # Get the current job for this task
            transfer_job = EssDiveTransfer.objects.all().get(id=run_id)
            assert ngt_id == transfer_job.dataset.data_set_id(), f"Expected {ngt_id} got {transfer_job.dataset.data_set_id()} for run_id {run_id}"
            transfer_job.status = EssDiveTransfer.STATUS_RUNNING
            transfer_job.start_time = timezone.now()
            transfer_job.save()

            method = essdive_id and "PUT" or "POST"
            json_ld = crosswalk.transform(transfer_job.dataset)
            log.info(f"{essdive_id and 'Updating' or 'Creating'} ESS-DIVE dataset metadata with ESS-DIVE identifier {essdive_id}")

            # Prepare the multi part encoding to stream the data
            files_tuples_array = list()
            files_tuples_array.append(("json-ld", json.dumps(json_ld)))

            # Is this a data update?
            if transfer_job.type == EssDiveTransfer.TYPE_DATA:
                log.info(f"Uploading ESS-DIVE dataset file '{transfer_job.dataset.archive.path}' for ESS-DIVE identifier {essdive_id}")
                files_tuples_array.append(
                    ('data', (transfer_job.dataset.archive.name, open(transfer_job.dataset.archive.path, 'rb'))))

            encoder = MultipartEncoder(fields=files_tuples_array)
            # need to limit number of messages at each percent
            monitor_messages = []

            def _upload_progress(monitor: MultipartEncoderMonitor):
                """
                Callback for MultipartEncoder Monitor to log upload progress
                :param monitor: The monitor for this callback
                :return: None
                """
                # Determine percentage complete
                percent_complete = math.floor(monitor.bytes_read/monitor.len * 100)
                if percent_complete % 10 == 0 and percent_complete not in monitor_messages:
                    monitor_messages.append(percent_complete)
                    log.info(f"Upload progress {transfer_job.dataset.data_set_id()} - bytes {monitor.bytes_read} of {monitor.len} ({percent_complete}%) read")

            monitor = MultipartEncoderMonitor(encoder, _upload_progress)
            response = requests.request(method=method, url=f"{service_account.endpoint}/{essdive_id or ''}",
                                        headers={"Authorization": f"Bearer {service_account.secret}",
                                                 'Content-Type': monitor.content_type},
                                        data=monitor)

            json_response = response.json()

            # Return run information
            return {"run_id": run_id, "response": json_response, "status_code": response.status_code}
        except Exception as e:
            _raise_run_error(e, run_id)

    else:
        RunError(None, "run_id is missing from result")


@shared_task
def transfer_end(result):
    """
    Log the end of the ESS-DIVE Transfer task

    :param result:
    :return:
    """
    log.debug("inputs:{}".format(result))
    # Import the Django Model objects

    run_id = result.get("run_id", None)
    response = result.get("response", None)
    status_code = result.get("status_code", None)

    if run_id:

        try:

            # Get the ESS-DIVE account information
            service_account = ServiceAccount.objects.all().get(service=SERVICE_ACCOUNT_ESSDIVE)

            # Get the current model for this task
            transfer_job = EssDiveTransfer.objects.all().get(id=run_id)
            transfer_job.end_time = timezone.now()
            transfer_job.response = response

            if status_code == status.HTTP_200_OK or status_code == status.HTTP_201_CREATED:
                # Success
                transfer_job.status = EssDiveTransfer.STATUS_SUCCESS
                transfer_job.message = f"{transfer_job.dataset.data_set_id()} {transfer_job.get_type_display()} was transferred to {service_account.endpoint}"
            else:
                # Failed
                transfer_job.status = EssDiveTransfer.STATUS_FAILED
                transfer_job.message = f"{transfer_job.dataset.data_set_id()} {transfer_job.get_type_display()} transfer to {service_account.endpoint} failed."

            transfer_job.save()
            return {"run_id": run_id}
        except Exception as e:
            _raise_run_error(e, run_id)

    else:
        RunError(None, "run_id is missing from result")


def _raise_run_error(e, run_id):
    """
    Raises run error and logs to the transfer job record

    :param e:
    :param run_id:
    :param service_account:
    :return:
    """
    # Get the current model for this task
    service_account = ServiceAccount.objects.all().get(service=SERVICE_ACCOUNT_ESSDIVE)
    transfer_job = EssDiveTransfer.objects.all().get(id=run_id)
    transfer_job.end_time = timezone.now()
    transfer_job.status = EssDiveTransfer.STATUS_FAILED
    transfer_job.message = f"{transfer_job.dataset.data_set_id()} {transfer_job.get_type_display()} transfer to {service_account.endpoint} failed. - {str(e)}"
    transfer_job.save()
    raise RunError(run_id, str(e))