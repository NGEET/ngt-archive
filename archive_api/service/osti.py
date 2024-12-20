from dataclasses import dataclass
from typing import Optional

import requests
import xml.etree.ElementTree as ET

# Basic NGT to OST Mapping
from ngt_archive import settings

import archive_api
from archive_api.models import DataSet, Author, ServiceAccount
from archive_api.service.common import ServiceAccountException, FUNDER_DOE_BER

MAPPING = [('title', 'name', ""),
           ('contract_nos', 'doe_funding_contract_numbers', "None"),
           ('non-doe_contract_nos', 'doe_funding_contract_numbers', ""),
           ('originating_research_org', 'originating_institution', ""),
           ('description', 'description', ""),
           ('sponsor_org', 'funding_organizations', FUNDER_DOE_BER),
           ('related_resource', 'reference', "")]


@dataclass
class OSTIRecord:
    status: str
    site_url:  Optional[str]
    doi: Optional[str]
    doi_status: Optional[str]
    status_message: Optional[str]


def _submit(osti_xml) -> OSTIRecord:
    """
    Submit OSTI xml record
    :param dataset_id:
    :return:
    """

    try:
        doi_service = ServiceAccount.objects.get(service=0)

        headers = {'Content-Type': 'application/xml'}
        r = requests.post(doi_service.endpoint,
                          data=osti_xml,
                          headers=headers,
                          auth=(doi_service.identity, doi_service.secret))

        if r.status_code == 200:
            root = ET.fromstring(r.content)
            doi = root.find("./record/doi")
            doi_status = doi is not None and doi.get("status") or None
            record_status = root.find("./record/status")
            record_status_message = root.find("./record/status_message")
            site_url = root.find("./record/site_url")
            osti_record = OSTIRecord(status=record_status.text,
                              site_url=site_url is not None and site_url.text or None,
                              doi=doi is not None and f"https://doi.org/{doi.text}" or None,
                              doi_status=doi_status,
                              status_message=record_status_message is not None and record_status_message.text or None)
            if osti_record.doi and not osti_record.doi.startswith("https://doi.org/10.15486/ngt/"):
                raise ServiceAccountException(
                    f"Error in publish data; There was a problem minting the DOI - "
                    f"The doi, {osti_record.doi}, is not a valid doi", 0)
            if not osti_record or osti_record.status != "SUCCESS":
                raise ServiceAccountException(
                    f"Error in doi record - {osti_record.status_message}", 0)
            return osti_record
        else:
            raise ServiceAccountException(f"HTTP Status: {r.status_code} HTTP Response: {r.content}",
                                          doi_service.service)
    except archive_api.models.ServiceAccount.DoesNotExist:
        raise ServiceAccountException(f"Does not exist", 0)


def mint(dataset_id) -> Optional[OSTIRecord]:
    """
    Mint DOI for a dataset (no publish) if not doi exists

    :param dataset_id: the database identifier of the dataset to mint a doi for
    :return: OSTIRecord  or None if doi already exists for specifed dataset.
    :raise: Except if no `ServiceAccount` defintion exists or any unexpected errors occur
    :rtype: archive_api.service.common.ServiceAccountException
    """

    dataset = DataSet.objects.get(pk=dataset_id)
    if not dataset.doi:
        osti_record = _submit(str(to_osti_xml()))
        if osti_record:
            if osti_record.status == "SUCCESS":
                dataset.doi = osti_record.doi
                dataset._change_reason = "Mint DOI"
                dataset.save()
            return osti_record
    return None


def publish(dataset_id) -> OSTIRecord:
    """
    Publish a dataset. This publishes the metadata to OSTI.

    :param dataset_id: the database identifier of the dataset to mint a doi for
    :return: OSTIRecord
    :raises: archive_api.service.common.ServiceAccountException
    """
    dataset = DataSet.objects.get(pk=dataset_id)

    if not dataset.doi:
        osti_record = mint(dataset_id)
    else:
        osti_record = _submit(str(to_osti_xml(dataset_id)))

    dataset.refresh_from_db()
    # Only check the site url on publish
    if osti_record and dataset.doi and dataset.status >= dataset.STATUS_APPROVED:
        if osti_record.site_url != _get_site_url(dataset):
            raise ServiceAccountException(
                f"Error in publish data; There was a problem minting the DOI - "
                f"The site url, {osti_record.site_url}, does not match our record, {_get_site_url(dataset)}.", 0)
    return osti_record



def to_osti_xml(dataset_id=None):
    """
    Generate the OSTI XML from the NGEE-Tropics Dataset JSON. If
    no dataset_id is specified a dummy record is created

    :param identifier: The unique identifier for the dataset
    :return:
    """
    dataset = None
    if dataset_id:
        dataset = DataSet.objects.get(pk=dataset_id)

    # Create OSTI XML
    records = ET.Element('records')
    record = ET.SubElement(records, 'record')

    for k, v, default in MAPPING:
        value = dataset and getattr(dataset, v) or default
        _set_value(record, k, value)
    _set_value(record, 'product_nos', dataset and dataset.data_set_id() or "")

    # Leave Blank for new  -fill in XXX with existing DOI otherwise.
    if dataset and dataset.doi:
        # Get the OSTI if from the end of the DOI
        osti_id = dataset.doi.split("/")[-1]
        _set_value(record, 'osti_id', osti_id)

    # Should this dataset be published or reserved
    if dataset and dataset.publication_date and dataset.status == dataset.STATUS_APPROVED:
        _set_value(record, 'site_url', _get_site_url(dataset))
        _set_value(record, 'publication_date', dataset.publication_date.strftime("%Y"))
    elif dataset and not dataset.doi or dataset is None:
        # reserve a doi before publication or for a dummy dataset
        _set_value(record, 'set_reserved', "")

    # DataSet Type: Dataset Type refers to the main content of the
    # dataset. Only one value is allowed. Use the two-letter codes shown below:
    _set_value(record, 'dataset_type', 'SM')  # Specialized Mix

    # Auto-fill

    _set_value(record, 'contact_name', 'NGEE Tropics Archive Team, Support Organization')
    _set_value(record, 'contact_email', settings.ARCHIVE_API['EMAIL_NGEET_TEAM'])
    _set_value(record, 'contact_org', 'Lawrence Berkeley National Lab')
    _set_value(record, 'site_code', 'NGEE-TRPC')
    _set_value(record, 'doi_infix', 'ngt')
    _set_value(record, 'subject_categories_code', '54 ENVIRONMENTAL SCIENCES')
    _set_value(record, 'language', 'English')
    _set_value(record, 'country', "US")

    # Generate the Authors section
    if dataset:
        _creators(record, dataset)

    # Store OSTI XML
    return ET.tostring(records).decode()


def _set_value(record, name, value):
    """
    Sets the element value for the record

    :param record:
    :param name: name of the field
    :param value: value of the field to se
    :return: None
    """

    ET.SubElement(record, name).text = value


def _creators(record, dataset):
    """
    Generate the creators block

    :param record: The OSTI xml record
    :param dataset: The NGT Archive dataset to build creators for
    :return: None
    """
    if dataset:
        authors = Author.objects.filter(dataset_id=dataset.id)
        creators_block = ET.SubElement(record, 'creatorsblock')
        for a in authors:
            creator_detail = ET.SubElement(creators_block, 'creators_detail')
            _set_value(creator_detail, 'first_name', a.author.first_name)
            _set_value(creator_detail, 'last_name', a.author.last_name)
            _set_value(creator_detail, 'private_email', a.author.email)
            _set_value(creator_detail, 'affiliation_name', a.author.institution_affiliation)

def _get_site_url(dataset):
    """
    Build the site url from the dataset

    :param dataset: The NGT Archive dataset to build creators for
    :return: string representing the site url
    """
    return f'https://{settings.SERVICE_HOSTNAME}/dois/{dataset.data_set_id()}'