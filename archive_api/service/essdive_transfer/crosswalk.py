"""
NGEE-Tropics to ESS-DIVE Metacata crosswalk module


"""
import csv
import collections
import re
from io import StringIO

from typing import Dict, IO, List, Optional, TextIO, Tuple, Union

import logging

# NGEE-Tropics Project information
LOCATION_NOT_APPLICABLE = "N/A"
JSONLD_PROVIDER = {
    "identifier": {
      "@type": "PropertyValue",
      "propertyID": "ess-dive",
      "value": "a441fe85-5ac3-41b1-bbe5-46df92682609"
   }
}

# NGEE-Tropics Keywords
JSONLD_KEYWORDS = ["Next-Generation Ecosystem Experiements Tropics", "NGEE-T"]

# CC By 4 License
JSONLD_LICENSE = "http://creativecommons.org/licenses/by/4.0/"

# Funding Organization
JSONLD_FUNDER = {"name": "U.S. DOE > Office of Science > Biological and Environmental Research (BER)"}

DESCRIPTION_MIRROR_FORMAT = "This dataset was originally published on the NGEE Tropics Archive and is " \
                                        "being mirrored on ESS-DIVE for long-term archival"
DESCRIPTION_ACK_FORMAT = "Acknowledgement: {0}"
DESCRIPTION_ACK_FILE_FORMAT = "Please see the {0}_acknowledgements.txt " \
                              "file for a full listing of dataset acknowledgements."


def _dataset_creator(dataset):
    """
    Generates the ESS-DIVE creators from the NGEE-Tropics DataSet Authors

    :param dataset: the ngt dataset object
    :return: a list of data package author info (one dictionary per author) in ESS-DIVE JSON-LD format
    """

    creators = list()
    from archive_api.models import Author

    # Get Authors in the specified order
    for a in Author.objects.filter(dataset_id=dataset.id).order_by('order'):
        author = a.author
        person = dict()
        person["givenName"] = author.first_name
        person["familyName"] = author.last_name
        if author.institution_affiliation: person["affiliation"] = author.institution_affiliation
        if author.email: person['email'] = author.email
        if author.orcid: person['@id'] = author.orcid

        creators.append(person)

    return creators


def _dataset_contact_info(dataset):
    """
    Creates ESS-DIVE JSON-LD editor from the NGEE-Tropics dataset contact

    :param dataset: the ngt dataset json structure.
    :return: a list of data package contact info (one dictionary per author) in JSON-LD format
    """

    person = dict()
    person["givenName"] = dataset.contact.first_name
    person["familyName"] = dataset.contact.last_name
    if dataset.contact.institution_affiliation: person["affiliation"] = dataset.contact.institution_affiliation
    if dataset.contact.email: person['email'] = dataset.contact.email
    if dataset.contact.orcid: person['@id'] = dataset.contact.orcid

    return person


def _dataset_description(dataset) -> Tuple[List[str], bool]:
    """
    Transforms the dataset description. This will be a combination of the description and the
    acknowledgements

    **<5000 characters with acknowledgement**
    ```
    <description>

    This dataset was originally published on the NGEE Tropics Archive and is being mirrored on ESS-DIVE for long-term archival

    Acknowledgement: <acknowledgment>
    ```

    **>=5000 characters with acknowledgement**
    ```
    <description>

    This dataset was originally published on the NGEE Tropics Archive and is being mirrored on ESS-DIVE for long-term archival

    Please see the <NGT_ID>_acknowledgements.txt file for a full listing of dataset acknowledgements.
    ```

    :param dataset: the ngt dataset json structure.
    :return: The transformed description and acknowledgement (string) in JSON-LD format and a boolean telling whether and acknowledgement file
        is needed.
    """
    description = [dataset.description, DESCRIPTION_MIRROR_FORMAT]
    ack_file_needed = False
    if dataset.acknowledgement:
        description.append(DESCRIPTION_ACK_FORMAT.format(dataset.acknowledgement))

        if len(''.join(description)) >= 5000:
            ack_file_needed = True
            description[-1] = DESCRIPTION_ACK_FILE_FORMAT.format(dataset.data_set_id())

    return description, ack_file_needed


def _dataset_temporal(dataset):
    """
    Creates the ESS-DIVE JSON-LD Temporal Coverage from the NGEE-Tropics dataset start
    and end dates

    :param dataset: the ngt dataset json structure.
    :return: The time period the data was collected during (string) in JSON-LD format
    """

    temporal_coverage = {}

    if dataset.end_date is not None:
       temporal_coverage["endDate"] = dataset.end_date.strftime("%Y-%m-%d")

    if dataset.start_date is not None:
        temporal_coverage["startDate"] = dataset.start_date.strftime("%Y-%m-%d")

    return temporal_coverage


def _dataset_spatial(dataset):
    """
    Creates the ESS-DIVE JSON-LD Spatial Coverage from the NGEE-Tropics dataset sites array

    :param dataset: the ngt dataset json structure.
    :return: dataset geographic description and bounding box coordinates in JSON-LD format
    """

    spatial_coverage = list()

    for location in dataset.sites.all():

        if location.site_id == LOCATION_NOT_APPLICABLE:
            continue

        # set x,y as bounding box coord for sites 1, 5, 12, 13, 14, 16, 20; which do not have bounding boxes.
        elif location.location_bounding_box_ul_latitude is None and location.location_latitude is not None:

            site = {
                "description": f"Site Name: {location.name}. Site ID: {location.site_id}. {location.description}",
                "geo": [
                    {
                        "name": "Northwest",
                        "latitude": location.location_latitude,
                        "longitude": location.location_longitude
                    },
                    {
                        "name": "Southeast",
                        "latitude": location.location_latitude,
                        "longitude": location.location_longitude
                    }
                ]
            }

        # set bounding box coordinates for remaining sites
        else:
            desc = f"Site Name: {location.name}. Site ID: {location.site_id}. "
            country = location.country and f"Located in {location.country}. " or ""

            site = {
                "description": f"{desc} {country} {location.description}",
                "geo": [
                    {
                        "name": "Northwest",
                        "latitude": location.location_bounding_box_ul_latitude,
                        "longitude": location.location_bounding_box_ul_longitude
                    },
                    {
                        "name": "Southeast",
                        "latitude": location.location_bounding_box_lr_latitude,
                        "longitude": location.location_bounding_box_lr_longitude
                    }
                ]
            }

        # after coordinates have been set in 'site' and description is added, add a URL for location if it has one
        if location.site_urls:
            add_url = f"For more information on this site, visit: {location.site_urls}"
            site["description"] = f"{site['description']} {add_url}"

        # add contact information if it exists
        if location.contacts.count() > 0:  # if the contacts key is not empty

            contact_description = " Site contact(s): "
            for con in location.contacts.all():
                contact_description += f" ({con.first_name} {con.last_name} <{con.email}>) "
            site["description"] = f"{site['description']} {contact_description}"

        spatial_coverage.append(site)
    if len(spatial_coverage):
        return spatial_coverage

    return None


def dataset_transform(dataset) -> Tuple[Dict, Optional[TextIO]]:
    """
    Transform NGEE-Tropics DataSet to ESSDIVE JSON-LD

    :param dataset: NGEET JSON
    :return: The JSON-LD and acknowledgements file point (if needed)
    """
    # start log
    logging.info('Transforming package to ESS-DIVE JSON-LD')

    # ---- alternate doi ----
    alternate_name = dataset.data_set_id()

    # ---- title, abstract, acknowledgement, publication date, funding program, DOI ----
    name = dataset.name
    submission_date = dataset.publication_date and dataset.publication_date.strftime("%Y-%m-%d") or None
    doi = dataset.doi

    description, ack_file_need = _dataset_description(dataset)

    # ---- related reference ----

    # Strip empty lines (ESS-DIVE api does not allow that for these fields)
    citation = dataset.reference and [r for r in dataset.reference.split('\n') if r] or list()
    if dataset.additional_reference_information:
        citation.append(f"Additional information about citations:")
        citation.extend([r for r in dataset.additional_reference_information.split("\n") if r])

    # ---- creators ----
    creators = _dataset_creator(dataset)

    # ---- editor ----
    editor = _dataset_contact_info(dataset)

    # ---- _dataset_temporal coverage ---
    temporal_coverage = _dataset_temporal(dataset)

    # --- _dataset_spatial coverage ---
    spatial_coverage = _dataset_spatial(dataset)

    # --- variables ---
    variable_measured = list()

    for variable in dataset.variables.all():
        variable_measured.append(variable.name)

    # --- methods ---
    measurement_technique = None
    if dataset.qaqc_method_description is not None:
        measurement_technique = dataset.qaqc_method_description and [r for r in dataset.qaqc_method_description .split('\n') if r] or list()

    # --- Funding Organization and Contract Numbers ---
    funders = [JSONLD_FUNDER]
    if dataset.funding_organizations:
        # if there are line breaks, commas, or semicolons, we assume multiple funders
        for f in re.split('[\n,;]', dataset.funding_organizations):
            funders.append({"name": f.strip()})

    # --- DOE Funding Contract Numbers --
    awards = None
    if dataset.doe_funding_contract_numbers:
        awards = re.split('[\n,;]', dataset.doe_funding_contract_numbers)

    # --- ASSIGN TO JSON-LD ----

    json_ld = {
        "@context": "http://schema.org/",
        "@type": "Dataset",
        "@id": doi,
        "name": name,
        "alternateName": alternate_name,
        "citation": citation,
        "description": description,
        "creator": creators,
        "datePublished": submission_date,
        "keywords": JSONLD_KEYWORDS,
        "variableMeasured": variable_measured,
        "license": JSONLD_LICENSE,
        "spatialCoverage": spatial_coverage,
        "funder": funders,
        "award": awards,
        "temporalCoverage": temporal_coverage,
        "editor": editor,
        "provider": JSONLD_PROVIDER,
        "measurementTechnique": measurement_technique
    }

    # remove empty fields
    for f in ["datePublished", "citation", "measurementTechnique", "spatialCoverage", "temporalCoverage", "@id"]:
        if not json_ld[f]: json_ld.pop(f)

    return json_ld, ack_file_need and acknowledgements_txt(dataset) or None


def locations_transform(dataset) -> List[collections.UserDict]:
    """
    Transform the specified datasets sites to
    the locations reporting format

    :param dataset:
    :return:
    """
    locations = []

    for site in dataset.sites.all():
        if site.site_id != LOCATION_NOT_APPLICABLE:

            # Prepare the notes with additional site information
            notes = []
            site.site_urls and notes.append(f"Site URL(s): {site.site_urls}")
            site.location_map_url and notes.append(f"Location Map URL: {site.location_map_url}")
            site.state_province and notes.append(f"State Province: {site.state_province}")

            locations.append(collections.UserDict(
                Submission_Contact_Name="; ".join([f"{c.first_name} {c.last_name}" for c in site.contacts.all()]),
                Submission_Contact_Email="; ".join([c.email for c in site.contacts.all()]),
                Location_ID=site.site_id,
                Description=site.description,
                Latitude=site.location_latitude,
                Longitude=site.location_longitude,
                Elevation=site.location_elevation,
                Location_Alias=site.name,
                Parent_Location_ID="",
                UTC_Offset=site.utc_offset,
                Country=site.country,
                Notes="; ".join(notes)))

    for plot in dataset.plots.all():
        # Prepare the notes with additional information
        notes = []
        plot.location_kmz_url and notes.append(f"Plot Location KMZ URL: {plot.location_kmz_url}")
        plot.size and notes.append(f"Plot Size: {plot.size}")

        locations.append(collections.UserDict(
            Submission_Contact_Name="; ".join([f"{c.first_name} {c.last_name}" for c in plot.site.contacts.all()]),
            Submission_Contact_Email="; ".join([c.email for c in plot.site.contacts.all()]),
            Location_ID=plot.plot_id,
            Description=plot.description,
            Latitude=plot.site.location_latitude,
            Longitude=plot.site.location_longitude,
            Elevation=plot.location_elevation,
            Location_Alias=plot.name,
            Parent_Location_ID=plot.site.site_id,
            UTC_Offset=plot.site.utc_offset,
            Country=plot.site.country,
            Notes="; ".join(notes)))

    return locations


def locations_csv(dataset) -> Optional[TextIO]:
    """
    Returns a file pointer to a locations csv for the specified
    dataset. Returns None if there were no locations

    :param dataset:
    :return: File Pointer
    """
    # Transform the locations file
    locations_json = locations_transform(dataset)
    if len(locations_json) > 0:
        # Prepare the StringIO object for writing
        locations_fp = StringIO()
        json_to_csv(locations_fp, locations_json)

        return locations_fp
    return None


def acknowledgements_txt(dataset) -> Optional[TextIO]:
    """
    Returns a file pointer to a acknowledgements text file for the specified
    dataset. Returns None if the transformed dataset description is < 5000 characters.

    :param dataset:
    :return: File Pointer
    """
    # Transform the acknowledgement file
    if len(dataset.acknowledgement) > 0:
        # Prepare the StringIO object for writing
        ack_fp = StringIO()
        ack_fp.write(dataset.acknowledgement)
        ack_fp.seek(0)
        return ack_fp
    return None


def json_to_csv(f: TextIO, json_obj: List[Union[collections.UserDict, dict, Dict]]):
    """
    Write the locations json as a csv file
    :param f: file to write to
    :param json_obj:
    :return:
    """

    # Write the CSV file to the io object
    writer = csv.DictWriter(f, fieldnames=list(json_obj[0].keys()))
    writer.writeheader()
    for location in json_obj:
        writer.writerow(location)

    # Now reset the io to the first position
    f.seek(0)