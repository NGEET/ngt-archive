from django.db import models

# Create your models here.

class DataSet(models.Model):
    """
    DataSet defines the metadata for the archived files.

    """

    data_set_id = models.CharField(max_length=20, blank=False)
    description = models.TextField()

