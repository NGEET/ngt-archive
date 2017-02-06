import mimetypes

import os
import django.contrib.auth.models
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.db import transaction
from django.conf import settings
from rest_framework.exceptions import ValidationError


class DatasetArchiveField( models.FileField):

        CONTENT_TYPES = ["application/zip", "application/x-bzip2",
                     "application/gzip", "application/x-lzip", "application/x-lzma",
                     "application/x-xz", "application/x-compress",
                     "application/x-compress", "application/x-7z-compressed",
                     "application/x-gtar", "application/x-rar-compressed"]

        def __init__(self, *args, **kwargs):
            """
            Override the parent constructor to set the allowed content_types

            :param args:
            :param kwargs:
            """

            self.content_types = self.CONTENT_TYPES
            super(DatasetArchiveField,self).__init__(*args,**kwargs)

        def clean(self, *args, **kwargs):
            """
            Override parent method to add checking for content type

            Parent method converts the value's type and run validation. Validation errors
            from to_python and validate are propagated. The correct value is
            returned if no error is raised.
            """
            data = super(DatasetArchiveField,self).clean(*args,**kwargs)

            try:
                content_type = mimetypes.guess_type(data.name)
                if content_type[0] not in self.content_types:
                    raise ValidationError('Filetype {} not supported. Allowed types: {}'.format(content_type[0],
                                                                                                ", ".join(
                                                                                                  self.content_types)))
            except AttributeError:
                raise ValidationError('Filetype unknown. Allowed types: {}'.format(", ".join(self.content_types)))

        def save(self, **kwargs):
            """
            Override parent to call the custom clean method

            :param kwargs:
            :return:
            """
            return super(DatasetArchiveField, self).save(**kwargs)


class DatasetArchiveStorage(FileSystemStorage):

    def __init__(self,*args, **kwargs):
        """
        Override parent constructor. If location is not set, set the
        `DATASET_ARCHIVE_ROOT`

        See `django.core.files.storage.FileSystemStorage` for more details.

        :param args:
        :param kwargs:
        """

        from django.conf import settings
        if "location" not in kwargs:
            kwargs["location"]=settings.ARCHIVE_API['DATASET_ARCHIVE_ROOT']
        if "base_url" not in kwargs:
            kwargs["base_url"] = settings.ARCHIVE_API['DATASET_ARCHIVE_URL']
        super(DatasetArchiveStorage, self).__init__(*args, **kwargs)


dataset_archive_storage = DatasetArchiveStorage()


STATUS_CHOICES = (
    (0, 'Draft'),
    (1, 'Submitted'),
    (2, 'Approved'),
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


def get_upload_path(instance, filename):
    """
    This generates the file upload path
    :param instance:
    :param filename:
    :return:
    """
    _, file_extension = os.path.splitext(filename)

    parent_dir_no = 0
    sub_dir_no = 0
    if instance.ngt_id > 0:
        parent_dir_no = int(int(instance.ngt_id / 100) * 100)
        sub_dir_no = int(int(instance.ngt_id/10) * 10)

    return os.path.join(
        "{parent_dir_no:04}/{sub_dir_no:04}/{data_set_id}/{version}/{data_set_id}_{version}{ext}".format(**{"data_set_id":instance.data_set_id(),
                             "parent_dir_no":parent_dir_no,
                             "sub_dir_no":sub_dir_no,
                             "version":instance.version,
                             "ext":file_extension}))


class MeasurementVariable(models.Model):
    name = models.CharField(max_length=50, unique=True)

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
        proxy=True

    @property
    def is_activated(self):
        active = (self.is_active and self.person is not None)
        return active or self.is_superuser

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
    user_role = models.IntegerField(choices=PERSON_ROLE_CHOICES,
                                    null=True, blank=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, null=True, blank=True)

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

    STATUS_DRAFT = 0
    STATUS_SUBMITTED = 1
    STATUS_APPROVED = 2

    def data_set_id(self):
        return "NGT{:04}".format(self.ngt_id)

    ngt_id = models.IntegerField()
    description = models.TextField(blank=True, null=True)
    version = models.CharField(max_length=15, default="0.0")

    status = models.IntegerField(choices=STATUS_CHOICES,
                              default=0)  # (draft [DEFAULT], submitted, approved)
    status_comment = models.TextField(blank=True, null=True)
    name = models.CharField(max_length=150, blank=True, null=True)
    doi = models.TextField(blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    qaqc_status = models.IntegerField(choices=QAQC_STATUS_CHOICES, blank=True, null=True)
    qaqc_method_description = models.TextField(blank=True, null=True)
    ngee_tropics_resources = models.NullBooleanField(blank=True,null=True)
    funding_organizations = models.TextField(blank=True, null=True)
    doe_funding_contract_numbers = models.CharField(max_length=100, blank=True, null=True)
    acknowledgement = models.TextField(blank=True, null=True)
    reference = models.TextField(blank=True, null=True)
    additional_reference_information = models.TextField(blank=True, null=True)
    originating_institution = models.TextField(blank=True, null=True)

    access_level = models.IntegerField(choices=ACCESS_CHOICES, default=0)
    additional_access_information = models.TextField(blank=True, null=True)
    submission_date = models.DateField(blank=True, null=True)

    # Owner is the person who created the dataset
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, editable=False, related_name='+')
    created_date = models.DateTimeField(editable=False, auto_now_add=True)
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, editable=False, related_name='+')
    modified_date = models.DateTimeField(editable=False, auto_now=True)

    # Relationships
    authors = models.ManyToManyField(Person, blank=True, related_name='+', through='Author')
    contact = models.ForeignKey(Person, on_delete=models.DO_NOTHING, blank=True, null=True)
    sites = models.ManyToManyField(Site, blank=True)
    plots = models.ManyToManyField(Plot, blank=True)
    variables = models.ManyToManyField(MeasurementVariable, blank=True)

    # CDIAC Import Fields
    cdiac_import = models.BooleanField(default=False)
    cdiac_submission_contact = models.ForeignKey(Person, related_name='+', on_delete=models.DO_NOTHING, blank=True,
                                                 null=True)

    archive = models.FileField(upload_to=get_upload_path, storage=dataset_archive_storage, null=True)

    class Meta:
        unique_together = ('ngt_id','version')
        permissions = (
            ("approve_submitted_dataset", "Can approve a 'submitted' dataset"),
            ("edit_own_draft_dataset", "Can edit own 'draft' dataset"),
            ("edit_all_submitted_dataset", "Can edit any 'submitted' dataset"),
            ("edit_all_draft_dataset", "Can edit any 'draft' dataset"),
            ("unsubmit_submitted_dataset", "Can unsubmit a 'submitted' dataset"),
            ("unapprove_approved_dataset", "Can unapprove a 'approved' dataset"),
            ("view_all_datasets", "Can view all datasets"),
            ("view_ngeet_approved_datasets", "Can view all approved NGEE Tropics datasets"),
            ("upload_large_file_dataset","Can upload a large file to a dataset")
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
            # if the ngt_id has not beent set then we need to get the next id
            if self.ngt_id is None and self.version == "0.0":
                # select_for_update Locks table for the rest of the transaction
                # nowait is honored if the db supports it.
                max_dataset = DataSet.objects.select_for_update(nowait=True).order_by('-ngt_id','-id')
                if max_dataset :
                    self.ngt_id = max_dataset[0].ngt_id + 1
                else: self.ngt_id=0 # only for the very first dataset
            super(DataSet, self).save(*args, **kwargs)

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return '{}-v{}: {}'.format(self.data_set_id(), self.version, self.name)

    def __repr__(self):
        return '<DataSet {}>'.format(self)




class Author(models.Model):
    """ Model for storing data about the Author relationship between DataSet and Person """
    author = models.ForeignKey(Person)
    dataset = models.ForeignKey(DataSet)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('dataset', 'order', 'author')
        ordering = ('dataset', 'order')


class DataSetDownloadLog(models.Model):
    """Logs archive downloads"""

    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.DO_NOTHING)
    dataset = models.ForeignKey(DataSet,on_delete=models.DO_NOTHING)
    dataset_status  = models.IntegerField(choices=STATUS_CHOICES)  # (draft [DEFAULT], submitted, approved)
    request_url = models.CharField(max_length=256)
    datetime = models.DateTimeField(editable=False, auto_now_add=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)