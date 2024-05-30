from datetime import datetime

import os

import django.contrib.auth.models
from django.conf import settings
from django.contrib.auth.models import Group
from django.core.files.storage import FileSystemStorage
from django.core.validators import RegexValidator
from django.db import models, transaction
from django.utils import timezone
from simple_history.models import HistoricalRecords
from django.core import validators

from cryptography.fernet import Fernet


class SecretField(models.Field):
    """
    Secret Field to be used to encryprt and decrypt. Encrypted
    data is stored as a binary value in the database.

    Design for this field based on:

       Yang, A. (2022, January 4). Using custom model fields to encrypt and decrypt data in Django.
       Medium. https://medium.com/finnovate-io/using-custom-model-fields-to-encrypt-and-decrypt-data-in-django-8255a4960b72
    """

    description = "Encrypt Service Account Secret"
    empty_values = [None, ""]

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('editable', False)
        # Set default values
        kwargs['max_length'] = "max_length" in kwargs and kwargs["max_length"] or 2048
        kwargs['blank'] = True
        kwargs['null'] = True
        super().__init__(*args, **kwargs)
        if self.max_length is not None:
            self.validators.append(validators.MaxLengthValidator(self.max_length))

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if self.editable:
            kwargs['editable'] = True
        else:
            del kwargs['editable']
        return name, path, args, kwargs

    def get_internal_type(self):
        return "CharField"

    def get_default(self):
        if self.has_default() and not callable(self.default):
            return self.default
        default = super().get_default()
        if default == '':
            return ""
        return default

    def get_prep_value(self, value):
        """
        Encrypt the value to be stored in the database

        Return field's value prepared for interacting with the database backend.

        Used by the default implementations of get_db_prep_save().
        :param value:
        :return:
        """
        # Instance the Fernet class with the key
        fernet = Fernet(self._get_secret_key())
        return fernet.encrypt(isinstance(value, (bytes, bytearray)) and value or value.encode()).decode()

    def from_db_value(self, value, expression, connection):
        """
        Decrypt the value coming from the database. Prepares the
        value coming from the database.

        :param value:
        :param expression:
        :param connection:
        :return:
        """
        if value is None:
            return value

        # Instance the Fernet class with the key
        fernet = Fernet(self._get_secret_key())
        return fernet.decrypt(isinstance(value, (bytes, bytearray)) and value or value.encode()).decode()

    def to_python(self, value):
        """
        Overrides models.Binaryfield.  We don't want to b64encode

        Convert the input value into the expected Python data type, raising
        django.core.exceptions.ValidationError if the data can't be converted.
        Return the converted value. Subclasses should override this.

        :param value:
        :return:
        """
        return value

    def value_to_string(self, obj):
        """
        Overrides modes.BinaryField.  There is no b64 encoding

        Secret data is encrypted
        """
        value = self.get_prep_value(self.value_from_object(obj))
        # Decode only if it is a byte array
        return isinstance(value, bytes) and value.decode() or value

    @staticmethod
    def _get_secret_key():
        """Get the Service account secret key from the settings"""
        return settings.ARCHIVE_API['SERVICE_ACCOUNT_SECRET_KEY'].encode()


class DatasetArchiveStorage(FileSystemStorage):
    def __init__(self, *args, **kwargs):
        """
        Override parent constructor. If location is not set, set the
        `DATASET_ARCHIVE_ROOT`

        See `django.core.files.storage.FileSystemStorage` for more details.

        :param args:
        :param kwargs:
        """

        from django.conf import settings
        if "location" not in kwargs:
            kwargs["location"] = settings.ARCHIVE_API['DATASET_ARCHIVE_ROOT']
        if "base_url" not in kwargs:
            kwargs["base_url"] = settings.ARCHIVE_API['DATASET_ARCHIVE_URL']
        super(DatasetArchiveStorage, self).__init__(*args, **kwargs)


dataset_archive_storage = DatasetArchiveStorage()

DATASET_STATUS_DRAFT = 0
DATASET_STATUS_SUBMITTED = 1
DATASET_STATUS_APPROVED = 2

SERVICE_ACCOUNT_OSTI = 0
SERVICE_ACCOUNT_ESSDIVE  = 1

STATUS_CHOICES = (
    (DATASET_STATUS_DRAFT, 'Draft'),
    (DATASET_STATUS_SUBMITTED, 'Submitted'),
    (DATASET_STATUS_APPROVED, 'Approved'),
)

QAQC_STATUS_CHOICES = (
    (0, 'None'),
    (1, 'Provisional QA-QC'),
    (2, 'Full QA-QC'),
)

ACCESS_CHOICES = (
    (0, 'Private'),
    (1, 'NGEE Tropics'),
    (2, 'Public'),
)

PERSON_ROLE_CHOICES = (
    (0, 'Team'),
    (1, 'Collaborator'),
)

SERVICE_ACCOUNT_CHOICES = (
    (SERVICE_ACCOUNT_OSTI, 'OSTI Elink'),
    (SERVICE_ACCOUNT_ESSDIVE, 'ESS-DIVE'),
)


def get_upload_path(instance, filename):
    """
    This generates the file upload path
    :param instance:
    :param filename:
    :return:
    """
    head, tail = os.path.split(filename)
    filename_base, filename_ext = os.path.splitext(tail)

    parent_dir_no = 0
    sub_dir_no = 0
    if instance.ngt_id > 0:
        parent_dir_no = int(int(instance.ngt_id / 100) * 100)
        sub_dir_no = int(int(instance.ngt_id / 10) * 10)

    return os.path.join(
        "{parent_dir_no:04}/{sub_dir_no:04}/{data_set_id}/{filename_base}_"
        "{now:%Y%m%d%H%M%S}{ext}".format(
            **{"data_set_id": instance.data_set_id(),
               "parent_dir_no": parent_dir_no,
               "sub_dir_no": sub_dir_no,
               "filename_base": filename_base,
               "now": datetime.now(),
               "ext": filename_ext}))


class MeasurementVariable(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return self.name

    def __repr__(self):
        return '<Contact {}>'.format(self)

    class Meta:
        ordering = ('name',)


class NGTUser(django.contrib.auth.models.User):
    def __unicode__(self):
        return self.get_full_name()

    class Meta:
        proxy = True

    @property
    def is_activated(self):
        active = (self.is_active and self.person is not None \
                  and len(self.groups.all()) > 0)
        return active or self.is_superuser

    def has_group(self, group_name):
        """ Determine if a user is in a group"""
        group = Group.objects.get(name=group_name)
        return group in self.groups.all()

    @property
    def person(self):
        try:
            return Person.objects.get(user=self)
        except Person.DoesNotExist:
            return None


class Person(models.Model):
    first_name = models.CharField(max_length=50, blank=False)
    last_name = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    institution_affiliation = models.CharField(max_length=100, blank=True)
    orcid = models.CharField(max_length=40, blank=True, validators=[
        RegexValidator("^https?://orcid.org/[0-9]{4}-?[0-9]{4}-?[0-9]{4}-?([0-9]{4}|[0-9]{3}X)(/)*$",
                       'Enter a valid ORCiD (e.g. https://orcid.org/xxxx-xxxx-xxxx-xxxx)')])
    user_role = models.IntegerField(choices=PERSON_ROLE_CHOICES,
                                    null=True, blank=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('first_name', 'last_name', 'institution_affiliation', 'email')
        ordering = ('last_name', 'first_name',)

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return '{}, {} - {}'.format(self.last_name, self.first_name, self.institution_affiliation)

    def __repr__(self):
        return '<Contact {}>'.format(self)


class Site(models.Model):
    site_id = models.CharField(unique=True, max_length=30)
    name = models.CharField(unique=True, max_length=300)
    description = models.TextField()
    country = models.CharField(max_length=100, blank=True)
    state_province = models.CharField(max_length=100, blank=True)
    utc_offset = models.IntegerField(blank=True, null=True)
    location_latitude = models.FloatField(blank=True, null=True)
    location_longitude = models.FloatField(blank=True, null=True)
    location_elevation = models.CharField(blank=True, max_length=30)
    location_map_url = models.URLField(blank=True, null=True)
    location_bounding_box_ul_latitude = models.FloatField(blank=True, null=True)
    location_bounding_box_ul_longitude = models.FloatField(blank=True, null=True)
    location_bounding_box_lr_latitude = models.FloatField(blank=True, null=True)
    location_bounding_box_lr_longitude = models.FloatField(blank=True, null=True)
    site_urls = models.TextField(blank=True, null=True)
    contacts = models.ManyToManyField(Person)
    pis = models.ManyToManyField(Person, related_name='+')
    submission = models.ForeignKey(Person, on_delete=models.DO_NOTHING, related_name='+')
    submission_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return '{} - {}'.format(self.site_id, self.name)

    def __repr__(self):
        return '<Site {}>'.format(self)

    class Meta:
        ordering = ('site_id', 'name')


class Plot(models.Model):
    plot_id = models.CharField(max_length=30, unique=True)
    name = models.CharField(unique=True, max_length=150)
    description = models.TextField()
    size = models.CharField(max_length=100, blank=True, null=True, )
    location_elevation = models.CharField(blank=True, null=True, max_length=30)
    location_kmz_url = models.URLField(blank=True, null=True, )
    pi = models.ForeignKey(Person, on_delete=models.DO_NOTHING, blank=True, null=True)
    site = models.ForeignKey(Site, on_delete=models.DO_NOTHING)
    submission = models.ForeignKey(Person, on_delete=models.DO_NOTHING, related_name='+')
    submission_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return '{} - {}'.format(self.site.site_id, self.plot_id)

    def __repr__(self):
        return '<Plot {}>'.format(self)

    class Meta:
        ordering = ('plot_id', 'name')


class DataSet(models.Model):
    ACCESS_PRIVATE = 0
    ACCESS_NGEET = 1
    ACCESS_PUBLIC = 2

    STATUS_DELETED = -1  # this does not show up in any displays
    STATUS_DRAFT = 0
    STATUS_SUBMITTED = 1
    STATUS_APPROVED = 2

    def data_set_id(self):
        return "NGT{:04}".format(self.ngt_id)

    ngt_id = models.IntegerField()
    description = models.TextField(blank=True, null=True, max_length=4000)
    version = models.CharField(max_length=15, default="0.0")

    status = models.IntegerField(choices=STATUS_CHOICES,
                                 default=0)  # (draft [DEFAULT], submitted, approved)
    status_comment = models.TextField(blank=True, null=True)
    name = models.CharField(max_length=150, blank=True, null=True)
    doi = models.URLField(blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    qaqc_status = models.IntegerField(choices=QAQC_STATUS_CHOICES, blank=True, null=True)
    qaqc_method_description = models.TextField(blank=True, null=True)
    ngee_tropics_resources = models.BooleanField(blank=True, null=True)
    funding_organizations = models.TextField(blank=True, null=True, max_length=1024)
    doe_funding_contract_numbers = models.CharField(max_length=100, blank=True, null=True)
    acknowledgement = models.TextField(blank=True, null=True)
    reference = models.TextField(blank=True, null=True, max_length=2255)
    additional_reference_information = models.TextField(blank=True, null=True, max_length=2255)
    originating_institution = models.TextField(blank=True, null=True)

    access_level = models.IntegerField(choices=ACCESS_CHOICES, default=0)
    additional_access_information = models.TextField(blank=True, null=True)
    submission_date = models.DateTimeField(blank=True, null=True)
    publication_date = models.DateTimeField(blank=True, null=True)
    approval_date = models.DateTimeField(blank=True, null=True)

    managed_by = models.ForeignKey(settings.AUTH_USER_MODEL, editable=True, related_name='+', on_delete=models.CASCADE)
    created_date = models.DateTimeField(editable=False, auto_now_add=True)
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, editable=False, related_name='+', on_delete=models.CASCADE)
    modified_date = models.DateTimeField(editable=True, blank=True)

    # Relationships
    authors = models.ManyToManyField(Person, blank=True, related_name='+', through='Author')
    contact = models.ForeignKey(Person, on_delete=models.DO_NOTHING, blank=True, null=True)
    sites = models.ManyToManyField(Site, blank=True)
    plots = models.ManyToManyField(Plot, blank=True)
    variables = models.ManyToManyField(MeasurementVariable, blank=True)

    # CDIAC Import Fields
    cdiac_import = models.BooleanField(default=False)
    cdiac_submission_contact = models.ForeignKey(Person, related_name='+',
                                                 on_delete=models.DO_NOTHING, blank=True,
                                                 null=True)

    archive = models.FileField(upload_to=get_upload_path, storage=dataset_archive_storage,
                               null=True)

    history = HistoricalRecords(
        history_change_reason_field=models.TextField(null=True)
    )

    @property
    def citation(self):
        """Generate the citation for this dataset """
        author_list = ["{} {}".format(o.author.last_name, o.author.first_name[0]) for o in
                       self.author_set.all().order_by('order')]
        authors = "; ".join(author_list)

        citation_string = "Citation information not available currently. Contact dataset author(s) for citation or " \
                          "acknowledgement text."
        if self.doi and self.submission_date:
            citation_string = f'{ authors } ({self.submission_date:%Y}): { self.name }. { self.version }. ' \
                f'NGEE Tropics Data Collection. (dataset). { self.doi }'

        return citation_string

    @property
    def needs_review(self):
        """Does this data package need a review?  """
        return self.status == self.STATUS_DRAFT and \
               self.submission_date is not None

    @property
    def needs_approval(self):
        """Does this data package need an approval?  """
        return self.status == self.STATUS_SUBMITTED

    @property
    def is_published(self):
        """Is this dataset published"""
        return self.publication_date is not None and self.publication_date < timezone.now()

    class Meta:
        unique_together = ('ngt_id', 'version')
        ordering = ('-modified_date',)
        permissions = (
            ("approve_submitted_dataset", "Can approve a 'submitted' dataset"),
            ("edit_own_dataset", "Can edit own dataset"),
            ("edit_all_dataset", "Can edit any  dataset"),
            ("view_all_datasets", "Can view all datasets"),
            ("view_ngeet_approved_datasets", "Can view all approved NGEE Tropics datasets"),
            ("upload_large_file_dataset", "Can upload a large file to a dataset")
        )

    def save(self, *args, **kwargs):
        """
        Overriding save method to add logic for setting the ngt_id. Outwardly this is the derived
        field data_set_id

        :param args:
        :param kwargs:
        :return:
        """
        # Performing an atomic transaction when determining the ngt_id
        with transaction.atomic():
            # if the ngt_id has not been set then we need to get the next id
            if self.ngt_id is None and self.version == "0.0":
                # select_for_update Locks table for the rest of the transaction
                # nowait is honored if the db supports it.
                max_dataset = DataSet.objects.select_for_update(nowait=True).order_by('-ngt_id',
                                                                                      '-id')
                if max_dataset:
                    self.ngt_id = max_dataset[0].ngt_id + 1
                else:
                    self.ngt_id = 0  # only for the very first dataset

            # handle the modified date time if not set
            if "modified_date" not in kwargs:
                self.modified_date = timezone.now()
            else:
                self.modified_date = kwargs["modified_date"]
                del kwargs['modified_date']

            # prepend the default contract number if not set
            if self.doe_funding_contract_numbers is not None and self.doe_funding_contract_numbers.strip() != "":
                if "AC02-05CH11231" not in self.doe_funding_contract_numbers and \
                  "AC0205CH11231" not in self.doe_funding_contract_numbers:
                    self.doe_funding_contract_numbers = \
                        "DE-AC02-05CH11231, " + self.doe_funding_contract_numbers
            else:
                self.doe_funding_contract_numbers = "DE-AC02-05CH11231"

            super(DataSet, self).save(*args, **kwargs)

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return '{}-v{}: {}'.format(self.data_set_id(), self.version, self.name)

    def __repr__(self):
        return '<DataSet {}>'.format(self)


class Author(models.Model):
    """ Model for storing data about the Author relationship between DataSet and Person """
    author = models.ForeignKey(Person, on_delete=models.CASCADE)
    dataset = models.ForeignKey(DataSet, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('dataset', 'order', 'author')
        ordering = ('dataset', 'order')


class DataSetDownloadLog(models.Model):
    """Logs archive downloads"""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING)
    dataset = models.ForeignKey(DataSet, on_delete=models.DO_NOTHING)
    dataset_status = models.IntegerField(
        choices=STATUS_CHOICES)  # (draft [DEFAULT], submitted, approved)
    request_url = models.CharField(max_length=256)
    datetime = models.DateTimeField(editable=False, auto_now_add=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)


class ServiceAccount(models.Model):
    """
    Service acount model for storing credentials.
    """
    name = models.CharField(max_length=40)
    service = models.IntegerField(choices=SERVICE_ACCOUNT_CHOICES, unique=True)
    identity = models.CharField(max_length=40, blank=True, null=True)
    secret = SecretField(editable=True, max_length=2048)
    endpoint = models.URLField(null=False, blank=False)

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return f"{SERVICE_ACCOUNT_CHOICES[self.service][1]}({self.name})"

    def __repr__(self):
        return f'<ServiceAccount {self}>'


class EssDiveTransfer(models.Model):
    """
    ESS-DIVE Transfers
    """

    STATUS_REQUEST = 0
    STATUS_QUEUED = 1
    STATUS_RUNNING = 2
    STATUS_SUCCESS = 3
    STATUS_FAILED = 4
    STATUS_RETRY = 5

    STATUS_CHOICES = (
        (STATUS_REQUEST, "Requested"),
        (STATUS_QUEUED, "Queued"),
        (STATUS_RUNNING, "Running"),
        (STATUS_SUCCESS, "Success"),
        (STATUS_FAILED, "Failed"),
        (STATUS_RETRY, "Retry")
    )

    TYPE_METADATA = 0
    TYPE_DATA = 1

    TYPE_CHOICES = (
        (TYPE_METADATA, "Metadata"),
        (TYPE_DATA, "Data")
    )

    dataset = models.ForeignKey(DataSet, on_delete=models.DO_NOTHING, blank=False, null=False)
    type = models.IntegerField(choices=TYPE_CHOICES, blank=False)
    status = models.IntegerField(default=STATUS_REQUEST ,choices=STATUS_CHOICES,  blank=False)
    create_time = models.DateTimeField(auto_now_add=True, editable=False)
    start_time = models.DateTimeField(editable=True, null=True, blank=True)
    end_time = models.DateTimeField(editable=True, blank=True, null=True)
    message = models.TextField(blank=True, null=True)
    response = models.JSONField(null=True, blank=True)  # Change to native field

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return f"EssDiveTransfer({self.dataset.data_set_id()}, {EssDiveTransfer.TYPE_CHOICES[self.type][1]})"

    def __repr__(self):
        return str(self)

    class Meta:
        ordering = ('-id',)


