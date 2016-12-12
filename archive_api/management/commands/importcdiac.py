import glob
import mimetypes
import sys

import os
from django.contrib.auth.models import User
from django.core.files import File
from django.core.management.base import BaseCommand
from django.utils.datetime_safe import datetime

from archive_api.models import DataSet, Person, Site, Plot, MeasurementVariable, Author, get_upload_path, \
    DatasetArchiveField


class Command(BaseCommand):
    help = 'Import the CDIAC metadata file into NGT Archive service.'

    def add_arguments(self, parser):
        parser.add_argument('ornl-backup-dir', type=str)
        parser.add_argument('username', type=str)

    def handle(self, *args, **options):

        # Get the xml file
        backup_dir = options['ornl-backup-dir']
        if os.path.exists(backup_dir):
            metadata_files = glob.glob("{}/Metadata/*.xml".format(backup_dir))
            datafiles_dir = "{}/DataFiles".format(backup_dir)

            for xml_file in metadata_files:
                filename, filename_extension = os.path.splitext(xml_file)
                ngt_id = filename.split("_")[-1].replace("NGT","")
                dataset = self.extract_metadata(options, ngt_id, xml_file)

                datafiles = glob.glob('{}/*NGT{}*'.format(datafiles_dir,ngt_id))
                if not datafiles:
                    datafiles = glob.glob('{}/NGT{}*'.format(datafiles_dir, ngt_id))

                if not datafiles:
                    print("\t - NGT{} does not have a single datafile directory".format(ngt_id))
                else:

                    archive_files = os.listdir(datafiles[0])
                    archived = False
                    # Check to see if this is an archive file already
                    if len(archive_files) == 1:
                        content_type = mimetypes.guess_type(archive_files[0])
                        archive_file = os.path.join(datafiles[0], archive_files[0])
                        if content_type[0] in DatasetArchiveField.CONTENT_TYPES:
                            filename = get_upload_path(dataset, archive_file)
                            with open(archive_file, 'rb') as f:
                                dataset.archive.save(filename,
                                                     File(f))
                            dataset.save()
                            archived = True

                    if not archived:  # if not, zip files up and upload
                        import shutil
                        archive_file_base = "/tmp/NGT{}".format(ngt_id)
                        archive_file = shutil.make_archive(archive_file_base, 'zip', datafiles[0])
                        filename = get_upload_path(dataset, archive_file)
                        with open(archive_file, 'rb') as f:
                            dataset.archive.save(filename,
                                                 File(f))
                        dataset.save()



    def extract_metadata(self, options, ngt_id,xml_file):

        # Access the metadata elements
        from xml.dom import minidom
        xmldoc = minidom.parse(xml_file)
        metadata = xmldoc.getElementsByTagName('metadata')[0]
        ptcontac = xmldoc.getElementsByTagName('ptcontac')[0]
        # Get the username for created_by and modified by
        create_by = User.objects.get(username=options['username'])
        # Determine if the dataset already exists
        try:
            dataset = DataSet.objects.get(id=ngt_id)
            dataset.modified_by = create_by
        except DataSet.DoesNotExist:

            dataset = DataSet(id=int(ngt_id), created_by=create_by, modified_by=create_by)
            dataset.save()

        # Origin are the authors in order of precedence
        origins = xmldoc.getElementsByTagName('origin')
        i = 0
        Author.objects.filter(dataset_id=dataset.id).delete()
        for origin in origins:
            namesplit = origin.childNodes[0].data.split(" ")
            fname = namesplit[0]
            lname = namesplit[1]
            if len(namesplit) == 3:
                fname = " ".join(namesplit[0:1])
                lname = namesplit[2]
            try:
                people = Person.objects.get(first_name=fname, last_name=lname)
            except Person.DoesNotExist:
                people = Person(first_name=fname, last_name=lname)
                people.save()

            author_order = Author(author=people, dataset=dataset, order=i)
            author_order.save()
            i += 1

        ######################
        # Reference
        try:
            lworkcit = xmldoc.getElementsByTagName('lworkcit')[0]
            reference = lworkcit.getElementsByTagName('title')[0].childNodes[0].data
            dataset.reference = reference

            dataset.additional_reference_information = lworkcit.getElementsByTagName('othercit')[0].childNodes[0].data
        except IndexError:
            pass

        ##########################
        # Submission Contact
        fname, lname = ptcontac.getElementsByTagName("cntper")[0].childNodes[0].data.split(" ")
        email = ptcontac.getElementsByTagName("cntemail")[0].childNodes[0].data
        try:
            people = Person.objects.get(first_name=fname, last_name=lname)
            people.email = email
            people.save()
        except Person.DoesNotExist:
            people = Person(first_name=fname, last_name=lname, email=email)
            people.save()
        if people:
            dataset.contact = people
            dataset.save()
        dataset.name = metadata.getElementsByTagName("title")[0].childNodes[0].data
        print("** " + dataset.name)
        # Version
        # metadata.idinfo.citation.citeinfo.edition
        # Data to upload
        # metadata.idinfo.citation.citeinfo.onlink
        ###########
        # Abstract
        # metadata.idinfo.descript.abstract
        dataset.description = metadata.getElementsByTagName("abstract")[0].childNodes[0].data
        ################
        # Start Date
        # metadata.idinfo.timeperd.rngdates.begindate
        dataset.start_date = metadata.getElementsByTagName("begdate")[0].childNodes[0].data
        ################
        # End Date
        # metadata.idinfo.timeperd.rngdates.enddate
        try:
            dataset.end_date = metadata.getElementsByTagName("enddate")[0].childNodes[0].data
        except:
            pass

        ##################
        # Submission Date
        # metadata.metainfo.metd
        try:
            dt = datetime.strptime(metadata.getElementsByTagName("metd")[0].childNodes[0].data, '%m/%d/%Y')
            dataset.submission_date = dt
            dataset.save()
        except Exception as e:
            print(e, file=sys.stderr)
            exit(-1)

        ##################
        # Acknowledgement
        # metadata.idinfo.datacred
        try:
            dataset.acknowledgement = metadata.getElementsByTagName("datacred")[0].childNodes[0].data
        except:
            pass

        # metadata.idinfo.status.progress (per Michale Crow ORNL) - I am pretty sure that we
        # were no longer using this field,
        # but this is the description on it: "Choices are Preliminary, Accepted, Retired”.
        # I believe this was going to be used in the future workflow, or we decided to
        # remove it from the workflow.
        ##################
        # Site ID
        #   Using this to look up the site in the DB. All other site fields in the
        #   XML will be ignored.
        site_id = None
        try:
            site_ids = metadata.getElementsByTagName("siteid")[0].childNodes[0].data.split(";")
            for site_id in site_ids:
                site = Site.objects.get(site_id=site_id.lstrip().rstrip())
                dataset.sites.add(site)
                dataset.save()
        except Site.DoesNotExist:
            print("Site {} does not exist".format(site_id), file=sys.stderr)
            exit(-1)

        ##################
        # Plot IDs
        #   Using this to look up the plots in the DB. All other plot fields in the
        #   XML will be ignored.
        plot_id = None
        try:
            plots = metadata.getElementsByTagName("plotid")
            for p in plots:
                plot_id = p.childNodes[0].data
                plot = Plot.objects.get(plot_id=plot_id)
                dataset.plots.add(plot)
                dataset.save()
        except Plot.DoesNotExist:
            print("Plot {} does not exist".format(plot_id), file=sys.stderr)
            exit(-1)
        except IndexError:
            pass

        ##################
        # Access Level
        #  metadata.idinfo.keywords.acconst
        try:
            access_level = metadata.getElementsByTagName("acconst")[0].childNodes[0].data
            if access_level.lower() == 'private':
                dataset.access_level = 0
            elif access_level.lower() == 'preliminary qa-qc':
                dataset.access_level = 1
            elif access_level.lower() == 'full qa-qc':
                dataset.access_level = 2
        except IndexError:
            pass

        ##################
        # QAQC Status
        #  metadata.dataqual.attracc.attraccr
        try:
            qaqc_status = metadata.getElementsByTagName("attraccr")[0].childNodes[0].data
            dataset.qaqc_status = 0
            if qaqc_status == 'Full QA-QC':
                dataset.qaqc_status = 2
            elif qaqc_status == 'Preliminary QA-QC':
                dataset.qaqc_status = 1
        except:
            pass

        # metadata.dataqual.qattracc.attracce
        try:
            dataset.qaqc_method_description = metadata.getElementsByTagName("attracce")[0].childNodes[0].data
        except:
            pass

        ##################
        # Originating Institution
        org = metadata.getElementsByTagName("dsoriginst")[0].childNodes[0].data
        dataset.originating_institution = org
        ##################
        # Submission contact/ the person who logged in and saved the record
        #   metadata.mercury.topics.dataset.authfn
        fname = metadata.getElementsByTagName("authfn")[0].childNodes[0].data
        lname = metadata.getElementsByTagName("authln")[0].childNodes[0].data
        # save them as a contact
        try:
            cdiac_contact = Person.objects.get(first_name=fname, last_name=lname)
        except Person.DoesNotExist:
            cdiac_contact = Person(first_name=fname, last_name=lname)
            cdiac_contact.save()
        dataset.cdiac_submission_contact = cdiac_contact
        dataset.cdiac_import = True
        dataset.save()
        ##################
        # NGEE tropics resources
        #
        ngee_tropics_resources = metadata.getElementsByTagName("dsngt")[0].childNodes[0].data
        if ngee_tropics_resources.startswith("No NGEE Tropics Resources"):
            dataset.ngee_tropics_resources = False
        else:
            dataset.ngee_tropics_resources = True

        #######################
        # Funding Contract numbers
        #   metadata.mercury.tropics.dataset.dsspon
        try:
            dataset.doe_funding_contract_numbers = metadata.getElementsByTagName("dsspon")[0].childNodes[0].data
        except IndexError:
            pass

        #######################
        # Funding Organizations
        #   dsfundcntr
        dataset.funding_organizations = metadata.getElementsByTagName("dsfundcntr")[0].childNodes[0].data
        # ome_file_status
        status = metadata.getElementsByTagName("ome_file_status")[0].childNodes[0].data
        if status == 'finalApproved':
            dataset.status = 2
        elif status == 'submit':
            dataset.status = 1

        #######################
        # Measurement Variables
        #   themekey
        v = None
        try:
            variables = metadata.getElementsByTagName("themekey")[0].childNodes[
                0].data.split(",")
            for v in variables:
                if v == 'Dendrometer data':
                    v = 'Dendrometry'
                elif v == 'Gas exchange':
                    v = 'Leaf gas exchange'
                elif v == 'NEE':
                    v = 'Net Ecosystem Exchange (NEE)'
                elif v == 'Leaf PV Parameters':
                    v = 'Leaf pressure-volume (PV) parameters'
                elif v == 'Solar Radiation (net)':
                    v = 'Solar Radiation (net)'
                mv = MeasurementVariable.objects.get(name=v.lstrip().rstrip())
                dataset.variables.add(mv)
        except MeasurementVariable.DoesNotExist:
            print("Variable '{}' does not exist".format(v), file=sys.stderr)
        dataset.save()

        return dataset
