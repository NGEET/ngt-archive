from django.contrib.auth.models import User
from django.db import models

STATUS_CHOICES = (
    ('0', 'Draft'),
    ('1', 'Submitted'),
    ('2', 'Approved'),
)

QAQC_STATUS_CHOICES = (
    ('0', 'None'),
    ('1', 'Preliminary QA-QC'),
    ('2', 'Full QA-QC'),
)

ACCESS_CHOICES = (
    ('0', 'Private'),
    ('1', 'NGEE Tropics'),
    ('2', 'Public'),
)


class MeasurementVariable(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return self.name

    def __repr__(self):
        return '<Contact {}>'.format(self)


class Person(models.Model):
    first_name = models.CharField(max_length=50, blank=False)
    last_name = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    institution_affiliation = models.CharField(max_length=100, blank=True)

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


class Plot(models.Model):
    plot_id = models.CharField(max_length=30, unique=True)
    name = models.CharField(unique=True, max_length=50)
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


class DataSet(models.Model):
    # TODO: understand how dataset Id is generated

    def data_set_id(self):
        return "NGT{}".format(self.id)

    description = models.TextField(blank=True, null=True)

    status = models.CharField(max_length=1, choices=STATUS_CHOICES,
                              default='0')  # (draft [DEFAULT], submitted, approved)
    status_comment = models.TextField(blank=True, null=True)
    name = models.CharField(unique=True, max_length=50, blank=True, null=True)
    doi = models.TextField(blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    qaqc_status = models.CharField(max_length=1, choices=QAQC_STATUS_CHOICES, blank=True, null=True)
    qaqc_method_description = models.TextField(blank=True, null=True)
    ngee_tropics_resources = models.BooleanField(default=False)
    funding_organizations = models.TextField(blank=True, null=True)
    doe_funding_contract_numbers = models.CharField(max_length=100, blank=True, null=True)
    acknowledgement = models.TextField(blank=True, null=True)
    reference = models.TextField(blank=True, null=True)
    additional_reference_information = models.TextField(blank=True, null=True)

    # TODO: Access levels: public, private, NGEE Tropics
    access_level = models.CharField(max_length=1, choices=ACCESS_CHOICES, default='0')
    additional_access_information = models.TextField(blank=True, null=True)
    submission_date = models.DateTimeField(blank=True, null=True)

    # Owner is the person who created the dataset
    created_by = models.ForeignKey(User, editable=False, related_name='+')
    created_date = models.DateTimeField(editable=False, auto_now_add=True)
    modified_by = models.ForeignKey(User, editable=False, related_name='+')
    modified_date = models.DateTimeField(editable=False, auto_now=True)

    # file = models.FileField()

    # Relationships
    authors = models.ManyToManyField(Person, blank=True, related_name='+')
    contact = models.ForeignKey(Person, on_delete=models.DO_NOTHING, blank=True, null=True)
    sites = models.ManyToManyField(Site, blank=True)
    plots = models.ManyToManyField(Plot, blank=True)
    variables = models.ManyToManyField(MeasurementVariable, blank=True)

    class Meta:
        permissions = (
            ("approve_submitted_dataset", "Can approve a 'submitted' dataset"),
            ("edit_draft_dataset", "Can edit a 'draft' dataset"),
            ("unsubmit_submitted_dataset", "Can unsubmit a 'submitted' dataset"),
            ("unapprove_approved_dataset", "Can unapprove a 'approved' dataset"),
            ("delete_draft_dataset", "Can delete a 'draft' dataset"),
            ("delete_submitted_dataset", "Can delete a 'submitted' dataset")
        )
