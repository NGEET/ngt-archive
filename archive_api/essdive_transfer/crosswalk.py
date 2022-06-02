"""
NGEE-Tropics to ESS-DIVE Metacata crosswalk module


"""
import logging

# NGEE-Tropics Project information
JSONLD_PROVIDER = {
    "name": "Next-Generation Ecosystem Experiments (NGEE) Tropics",
    "member": {
        "@id": "http://orcid.org/0000-0003-3983-7847",
        "givenName": "Jeffrey",
        "familyName": "Chambers",
        "email": "jchambers@lbl.gov",
        "institution": "Lawrence Berkeley National Laboratory",
        "jobTitle": "Principal Investigator"
    }
}

# NGEE-Tropics Keywords
JSONLD_KEYWORDS = ["Next-Generation Ecosystem Experiements Tropics", "NGEE-T"]

# CC By 4 License
JSONLD_LICENSE = "http://creativecommons.org/licenses/by/4.0/"

# Funding Organization
JSONLD_FUNDER = {"name": "U.S. DOE > Office of Science > Biological and Environmental Research (BER)"}


def creator(dataset):
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


def contact_info(dataset):
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


def temporal(dataset):
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


def spatial(dataset):
    """
    Creates the ESS-DIVE JSON-LD Spatial Coverage from the NGEE-Tropics dataset sites array

    :param dataset: the ngt dataset json structure.
    :return: dataset geographic description and bounding box coordinates in JSON-LD format
    """

    spatial_coverage = list()

    for location in dataset.sites.all():

        if location.name == "N/A":
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

    return spatial_coverage


def transform(dataset):
    """
    Transform NGEE-Tropics DataSet to ESSDIVE JSON-LD

    :param dataset: NGEET JSON
    :return:
    """
    # start log
    logging.info('Transforming package to ESS-DIVE JSON-LD')

    # ---- alternate doi ----
    alternate_name = dataset.data_set_id()

    # ---- title, abstract, acknowledgement, publication date, funding program, DOI ----
    name = dataset.name
    submission_date = dataset.publication_date and dataset.publication_date.strftime("%Y-%m-%d") or None
    doi = dataset.doi

    description = [dataset.description, "This dataset was originally published on the NGEE Tropics Archive and is "
                                        "being mirrored on ESS-DIVE for long-term archival"]
    if dataset.acknowledgement:
        description.append(f"Acknowledgement: {dataset.acknowledgement}")

    # ---- related reference ----

    citation = dataset.reference and dataset.reference.split('\n\n') or list()
    if dataset.additional_reference_information:
        citation.append(f"Additional information about citations: {dataset.additional_reference_information}")

    # ---- creators ----
    creators = creator(dataset)

    # ---- editor ----
    editor = contact_info(dataset)

    # ---- temporal coverage ---
    temporal_coverage = temporal(dataset)

    # --- spatial coverage ---
    spatial_coverage = spatial(dataset)

    # --- variables ---
    variable_measured = list()

    for variable in dataset.variables.all():
        variable_measured.append(variable.name)

    # --- methods ---
    measurement_technique = None
    if dataset.qaqc_method_description is not None:
        measurement_technique = [dataset.qaqc_method_description]

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
        "funder": JSONLD_FUNDER,
        "temporalCoverage": temporal_coverage,
        "editor": editor,
        "provider": JSONLD_PROVIDER,
        "measurementTechnique": measurement_technique
    }

    # remove empty fields
    for f in ["datePublished", "citation", "measurementTechnique", "spatialCoverage", "spatialCoverage", "temporalCoverage", "@id"]:
        if not json_ld[f]: json_ld.pop(f)

    return json_ld
