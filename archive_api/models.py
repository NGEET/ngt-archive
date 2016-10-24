from django.db import models


# STATUS_CHOICES = (
#     ('0', 'Draft'),
#     ('1', 'Submitted'),
#     ('2', 'Approved'),
# )
#
# QAQC_STATUS_CHOICES = (
# ('0', 'None'),
#     ('1', 'Preliminary QA-QC'),
#     ('2', 'Full QA-QC'),
# )


class MeasurementVariable(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return self.name

    def __repr__(self):
        return '<Contact {}>'.format(self)


class Contact(models.Model):
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
    contact = models.ForeignKey(Contact, on_delete=models.DO_NOTHING, blank=True, null=True)
    pi = models.ForeignKey(Contact, on_delete=models.DO_NOTHING, related_name='+', blank=True, null=True)
    submission = models.ForeignKey(Contact, on_delete=models.DO_NOTHING, related_name='+')
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
    pi = models.ForeignKey(Contact, on_delete=models.DO_NOTHING, blank=True, null=True)
    site = models.ForeignKey(Site, on_delete=models.DO_NOTHING)
    submission = models.ForeignKey(Contact, on_delete=models.DO_NOTHING, related_name='+')
    submission_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return '{} - {}'.format(self.site.site_id, self.plot_id)

    def __repr__(self):
        return '<Plot {}>'.format(self)


class DataSet(models.Model):
    # TODO: understand how dataset Id is generated
    data_set_id = models.CharField(max_length=20, blank=False)
    description = models.TextField()

# status = models.CharField(max_length=1, choices=STATUS_CHOICES)  #(draft, submitted, approved)
# status_comment = models.TextField()
# name = models.CharField(unique=True, max_length=50)
# doi = models.TextField()
# contact = models.ForeignKey(Contact, on_delete=models.DO_NOTHING)
#
# # TODO - does this need to be a datetime?
# start_date = models.DateField()
# end_date = models.DateField()
#
# qaqc_status = models.CharField(max_length=1, choices=QAQC_STATUS_CHOICES)
# qaqc_method_description = models.TextField()
# ngee_tropics_tesources = models.BooleanField()
# funding_organizations = models.TextField()
# doe_funding_contract_numbers = models.CharField(max_length=100)
# acknowledgement = models.TextField()
# reference = models.TextField()
# additional_reference_information = models.TextField()
#
# # TODO: Access levels: public, private, NGEE Tropics
# #access_level = models.CharField(max_length=1, choices=)
# additional_access_information = models.TextField()
# submission_date = models.DateTimeField(auto_created=True)
# lastModified_date = models.DateTimeField(auto_now=True)
#
# # TODO - figure out how to have created by and modified by users
# # createdBy
# # modifiedBy
# file = models.FileField()
#
# # Relationships
# sites = models.ManyToManyField(Site)
# plots = models.ManyToManyField(Plot)
# variables = models.ManyToManyField(MeasurementVariable)
