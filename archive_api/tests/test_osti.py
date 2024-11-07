import os

import pytest
import requests
from django.core.management import call_command

from archive_api.service.common import ServiceAccountException
from archive_api.service.osti import mint, publish, to_osti_xml
from archive_api.models import  ServiceAccount


OSTI_XML = '<records><record><title>Data Set 3</title><contract_nos>None</contract_nos><non-doe_contract_nos /><originating_research_org /><description>Qui illud verear persequeris te. Vis probo nihil verear an, zril tamquam philosophia eos te, quo ne fugit movet contentiones. Quas mucius detraxit vis an, vero omnesque petentium sit ea. Id ius inimicus comprehensam.</description><sponsor_org>A few funding organizations for my self</sponsor_org><related_resource /><product_nos>NGT0002</product_nos><osti_id>8343947</osti_id><site_url>https://ngt-data.lbl.gov/dois/NGT0002</site_url><publication_date>2016</publication_date><dataset_type>SM</dataset_type><contact_name>NGEE Tropics Archive Team, Support Organization</contact_name><contact_email>NGEE Tropics Archive Test &lt;ngeet-team@testserver&gt;</contact_email><contact_org>Lawrence Berkeley National Lab</contact_org><site_code>NGEE-TRPC</site_code><doi_infix>ngt</doi_infix><subject_categories_code>54 ENVIRONMENTAL SCIENCES</subject_categories_code><language>English</language><country>US</country><creatorsblock><creators_detail><first_name>Luke</first_name><last_name>Cage</last_name><private_email>lcage@foobar.baz</private_email><affiliation_name>POWER</affiliation_name></creators_detail></creatorsblock></record></records>'
OSTI_XML_DUMMY = '<records><record><title /><contract_nos>None</contract_nos><non-doe_contract_nos /><originating_research_org /><description /><sponsor_org>U.S. DOE &gt; Office of Science &gt; Biological and Environmental Research (BER)</sponsor_org><related_resource /><product_nos /><set_reserved /><dataset_type>SM</dataset_type><contact_name>NGEE Tropics Archive Team, Support Organization</contact_name><contact_email>NGEE Tropics Archive Test &lt;ngeet-team@testserver&gt;</contact_email><contact_org>Lawrence Berkeley National Lab</contact_org><site_code>NGEE-TRPC</site_code><doi_infix>ngt</doi_infix><subject_categories_code>54 ENVIRONMENTAL SCIENCES</subject_categories_code><language>English</language><country>US</country></record></records>'
BASEPATH = os.path.dirname(__file__)


@pytest.fixture(scope='module')
def django_load_data(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command('loaddata', 'test_auth.json')
        call_command('loaddata', 'test_archive_api.json')
        ServiceAccount.objects.create(name="FooBar", service=0, identity="myuseraccount", secret="foobar",
                                      endpoint="http://foobar.baz")

@pytest.mark.django_db
@pytest.mark.parametrize("dataset_id,expected_osti_xml",
                         [(None, OSTI_XML_DUMMY),
                          (3, OSTI_XML)], ids=["OSTI-dummy", "OSTI-publish"])
def test_to_osti(django_load_data, dataset_id, expected_osti_xml):
    """Test the generation of OSTI dummy xml"""
    osti_xml = to_osti_xml(dataset_id)
    print(osti_xml)
    assert osti_xml == expected_osti_xml


@pytest.mark.django_db
@pytest.mark.parametrize("dataset_id, response_file, doi, doi_funcion",
                         [(2, "osti_response_publish.xml", 'https://doi.org/10.15486/ngt/1525114', publish),
                          (1, "osti_response_mint.xml", "https://doi.org/10.15486/ngt/1525121", mint)],
                         ids=["publish", "mint"])
def test_osti(django_load_data, monkeypatch, dataset_id, response_file, doi, doi_funcion):
    """Test publish"""

    def mock_post(*args, **kwargs):
        return type('Dummy', (object,), {
            "content": open(os.path.join(BASEPATH, response_file)).read(),
            "status_code": 200,
            "url": "/testurl"})

    monkeypatch.setattr(requests, 'post',
                        mock_post)

    osti_record = doi_funcion(dataset_id)
    assert osti_record
    assert osti_record.status == "SUCCESS"
    assert osti_record.doi_status == "PENDING"
    assert osti_record.doi == doi


@pytest.mark.django_db
@pytest.mark.parametrize("status_code",
                         [(200),
                          (500)])
def test_osti_error(django_load_data, monkeypatch, status_code):
    """Test publish"""

    osti_response =  open(os.path.join(BASEPATH, "osti_response_error.xml")).read()

    def mock_post(*args, **kwargs):
        assert "auth" in kwargs
        assert kwargs["auth"] == ("myuseraccount", 'foobar')

        return type('Dummy', (object,), {
            "content": osti_response,
            "status_code": status_code,
            "url": "/testurl"})

    monkeypatch.setattr(requests, 'post', mock_post)

    with pytest.raises(ServiceAccountException) as exec_info:
        publish(2)

    if status_code == 200:
        assert str(exec_info.value) == ('Service Account OSTI Elink: Error in doi record - Title is required.; DOE '
                                        'Contract/Award Number(s) is required.; Author(s) is required.; Publication '
                                        'Date is required.; Sponsoring Organization is required.; Missing required '
                                        'URL.')
    else:
        assert str(exec_info.value) == 'Service Account OSTI Elink: HTTP Status: 500 HTTP Response: '+osti_response


@pytest.mark.django_db
def test_osti_service_not_exist(django_load_data):
    """Test osti service does not exist"""
    from archive_api.models import ServiceAccount
    ServiceAccount.objects.all().delete()
    pytest.raises(ServiceAccountException, publish, 2)


@pytest.mark.django_db
def test_osti_needs_doi(django_load_data, monkeypatch):
    """Test osti service raises a service exception when publishing and there is no DOI"""

    def mock_post(*args, **kwargs):

        assert "auth" in kwargs
        assert kwargs["auth"] == ("myuseraccount", 'foobar')

        return type('Dummy', (object,), {
            "content": open(os.path.join(BASEPATH, "osti_response_error.xml")).read(),
            "status_code": 200,
            "url": "/testurl"})

    monkeypatch.setattr(requests, 'post', mock_post)
    pytest.raises(ServiceAccountException, publish, 1)


@pytest.mark.django_db
def test_osti_mint_not_needed(django_load_data):
    """Test osti mint returns None.  The dataset already has a DOI """
    assert mint(2) is None



@pytest.mark.django_db
@pytest.mark.parametrize("osti_xml, error_message",
                         [("osti_response_publish_error_site_url.xml",
                           ('Service Account OSTI Elink: Error in publish data; There was a problem '
                            'minting the DOI - The site url, https://vchendrix/dois/NGT0001, does not '
                            'match our record, https://ngt-data.lbl.gov/dois/NGT0002.')
                           ),
                          ("osti_response_publish_error_doi.xml",
                           ('Service Account OSTI Elink: Error in publish data; There was a problem '
                            'minting the DOI - The doi, https://doi.org/10.15486/fob/1525114, is not a '
                            'valid doi'))],
                         ids=['site_url', 'doi'])
def test_osti_publish_errors(django_load_data, monkeypatch, osti_xml, error_message):
    """Test publish errors"""

    def mock_post(*args, **kwargs):
        assert "auth" in kwargs
        assert kwargs["auth"] == ("myuseraccount", 'foobar')

        return type('Dummy', (object,), {
            "content": open(os.path.join(BASEPATH, osti_xml)).read(),
            "status_code": 200,
            "url": "/testurl"})

    monkeypatch.setattr(requests, 'post', mock_post)

    with pytest.raises(ServiceAccountException) as exec_info:
        publish(3)


    assert str(exec_info.value) == error_message
