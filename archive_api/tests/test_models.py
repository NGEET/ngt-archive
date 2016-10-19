from django.test import TestCase
from archive_api.models import DataSet


class DataSetTestCase(TestCase):
    def setUp(self):
        DataSet.objects.create(data_set_id="Foo",description="A Foo dataset")
        DataSet.objects.create(data_set_id="Bar",description="A Bar dataset")

    def test_get(self):
        """Assert that the DataSets were created"""
        foo = DataSet.objects.get(data_set_id="Foo")
        bar = DataSet.objects.get(data_set_id="Bar")
        self.assertEqual(bar.data_set_id, "Bar")
        self.assertEqual(foo.data_set_id, 'Foo')

    def test_update(self):
        """ Assert that the DataSet was updated """
        foo = DataSet.objects.get(data_set_id="Foo")

        foo.data_set_id="FooBar"
        foo.save()

        foo = DataSet.objects.get(data_set_id="FooBar")
        self.assertIsNotNone(foo)
        self.assertEqual(foo.data_set_id, 'FooBar')
        self.assertEqual(foo.description, 'A Foo dataset')

    def test_list(self):
        """Assert that all DataSets were found"""
        """Assert that all DataSets were found"""
        data_sets = DataSet.objects.all()
        self.assertEqual(len(data_sets),2)