from django.contrib.auth.models import User

from archive_api.models import DataSet, Site, Plot, Person, MeasurementVariable
from django.test import TestCase


class DataSetTestCaseNew(TestCase):
    fixtures = ('test_auth.json', )

    def setUp(self):
        self.user = User.objects.get(pk=1)

    def test_create(self):

        id1 = DataSet.objects.create(description="A Fantastic dataset", created_by=self.user, modified_by=self.user).id
        id2=DataSet.objects.create(description="Another Fantastic dataset", created_by=self.user, modified_by=self.user).id
        id3= DataSet.objects.create(description="A Fantastic dataset", created_by=self.user, modified_by=self.user,
                               ngt_id=0, version="1.0").id
        id4 = DataSet.objects.create(description="A Third dataset", created_by=self.user, modified_by=self.user).ngt_id

        # Test NGT increment
        self.assertEqual(2,id4)

        foo = DataSet.objects.get(pk=id1)
        self.assertEqual(foo.ngt_id, 0)
        self.assertEqual(foo.version,"0.0")
        self.assertEqual(foo.description,"A Fantastic dataset")

        foo = DataSet.objects.get(pk=id2)
        self.assertEqual(foo.ngt_id, 1)
        self.assertEqual(foo.version, "0.0")
        self.assertEqual(foo.description, "Another Fantastic dataset")

        foo = DataSet.objects.get(pk=id3)
        self.assertEqual(foo.ngt_id, 0)
        self.assertEqual(foo.version, "1.0")
        self.assertEqual(foo.description, "A Fantastic dataset")

        from django.db.utils import IntegrityError
        self.assertRaises(IntegrityError,DataSet.objects.create,description="Another Fantastic dataset", created_by=self.user, modified_by=self.user,
                               version="1.0")


class DataSetTestCase(TestCase):
    fixtures = ('test_auth.json', 'test_archive_api.json',)
    def setUp(self):
        pass

    def test_get(self):
        """Assert that the DataSets were created"""
        foo = DataSet.objects.get(id=1)
        bar = DataSet.objects.get(id=2)
        self.assertEqual(foo.name, "Data Set 1")
        self.assertEqual(bar.name, "Data Set 2")

    def test_update(self):
        """ Assert that the DataSet was updated """
        foo = DataSet.objects.get(id=1)

        foo.name = "FooBar"
        foo.description = "A Foo dataset"
        foo.save()

        foo = DataSet.objects.get(id=1)
        self.assertIsNotNone(foo)
        self.assertEqual(foo.name, 'FooBar')
        self.assertEqual(foo.description, 'A Foo dataset')

    def test_list(self):
        """Assert that all DataSets were found"""
        data_sets = DataSet.objects.all()
        self.assertEqual(len(data_sets), 3)


class PersonTestCase(TestCase):
    def setUp(self):
        Person.objects.create(first_name="Mary", last_name="Cook", email="mcook@foobar.com",
                              institution_affiliation="FooBar")

    def test_get(self):
        """Assert that the Persons were created"""
        foo = Person.objects.get(first_name="Mary", last_name="Cook", email="mcook@foobar.com",
                                  institution_affiliation="FooBar")
        self.assertEqual(str(foo), "Cook, Mary - FooBar")

    def test_update(self):
        """ Assert that the Persons was updated """
        foo = Person.objects.get(first_name="Mary", last_name="Cook", email="mcook@foobar.com",
                                  institution_affiliation="FooBar")

        foo.first_name = "Jane"
        foo.save()

        foo = Person.objects.get(first_name="Jane", last_name="Cook", email="mcook@foobar.com",
                                 institution_affiliation="FooBar")
        self.assertIsNotNone(foo)
        self.assertEqual(str(foo), "Cook, Jane - FooBar")

    def test_list(self):
        """Assert that all Persons were found"""
        objs = Person.objects.all()
        self.assertEqual(len(objs), 1)


class MeasurementVariableTestCase(TestCase):
    def setUp(self):
        MeasurementVariable.objects.create(name="FooBar")

    def test_get(self):
        """Assert that the MeasurementVariable were created"""
        foo = MeasurementVariable.objects.get(name="FooBar")
        self.assertEqual(str(foo), "FooBar")

    def test_update(self):
        """ Assert that the MeasurementVariable was updated """
        foo = MeasurementVariable.objects.get(name="FooBar")

        foo.name = "FooBarBaz"
        foo.save()

        foo = MeasurementVariable.objects.get(name="FooBarBaz")
        self.assertIsNotNone(foo)
        self.assertEqual(str(foo), "FooBarBaz")

    def test_list(self):
        """Assert that all MeasurementVariable were found"""
        objs = MeasurementVariable.objects.all()
        self.assertEqual(len(objs), 1)


class SiteTestCase(TestCase):
    fixtures = ('test_auth.json', 'test_archive_api.json',)

    def setUp(self):
        submission = Person.objects.get(pk=1)
        Site.objects.create(site_id="XXXXXXX",
                            name="The name of the site",
                            description="Lorem ipsum dolor sit amet, eu eum ludus deleniti, "
                                        "agam scriptorem ex pri, in vide definitiones vis."
                                        " Mea ut ornatus alienum periculis. Eos noster dolorum "
                                        "liberavisse an. Quo dicam graeci aperiri an, te omnes assentior "
                                        "neglegentur eam, has et choro appetere voluptatibus. An ius vocibus "
                                        "recusabo, ridens abhorreant interpretaris per ei. Ne dicant vituperatoribus "
                                        "vel, autem nullam persius te eum, cu augue oratio copiosae mel. Per ea "
                                        "vero utamur, sed no cetero eligendi honestatis.",
                            country="Bangladesh",
                            state_province="",
                            utc_offset=0,
                            submission=submission,
                            site_urls="http://www.example.com/foo/bar")
        site = Site.objects.get(site_id="XXXXXXX")
        Plot.objects.create(name="The name of the plot",
                            description="Lorem ipsum dolor sit amet, eu eum ludus deleniti, "
                                        "agam scriptorem ex pri, in vide definitiones vis."
                                        " Mea ut ornatus alienum periculis. Eos noster dolorum "
                                        "liberavisse an. Quo dicam graeci aperiri an, te omnes assentior "
                                        "neglegentur eam, has et choro appetere voluptatibus. An ius vocibus "
                                        "recusabo, ridens abhorreant interpretaris per ei. Ne dicant vituperatoribus "
                                        "vel, autem nullam persius te eum, cu augue oratio copiosae mel. Per ea "
                                        "vero utamur, sed no cetero eligendi honestatis.",
                            size="5x5",
                            location_kmz_url="http://www.example.com/foo/bar",
                            submission=submission,
                            site=site)

    def test_get_site(self):
        """Assert that the Site was created"""
        foo = Site.objects.get(site_id="XXXXXXX")

        self.assertIsNotNone(foo)

    def test_get_plot(self):
        """Assert that the Plot was created"""
        foo = Plot.objects.get(name="The name of the plot", site__site_id="XXXXXXX")

        self.assertIsNotNone(foo)

    def test_update_siteplot(self):
        """ Assert that the Site and Plot were updated """
        foo = Site.objects.get(site_id="XXXXXXX")

        foo.site_id = "YYYYYYY"
        foo.save()
        foo = Site.objects.get(site_id="YYYYYYY")
        self.assertIsNotNone(foo)

        self.assertEqual(foo.site_id, 'YYYYYYY')
        self.assertEqual(foo.name, 'The name of the site')
        self.assertEqual(foo.description, "Lorem ipsum dolor sit amet, eu eum ludus deleniti, "
                                          "agam scriptorem ex pri, in vide definitiones vis."
                                          " Mea ut ornatus alienum periculis. Eos noster dolorum "
                                          "liberavisse an. Quo dicam graeci aperiri an, te omnes assentior "
                                          "neglegentur eam, has et choro appetere voluptatibus. An ius vocibus "
                                          "recusabo, ridens abhorreant interpretaris per ei. Ne dicant vituperatoribus "
                                          "vel, autem nullam persius te eum, cu augue oratio copiosae mel. Per ea "
                                          "vero utamur, sed no cetero eligendi honestatis.")
        self.assertEqual(foo.country, "Bangladesh")
        self.assertEqual(foo.state_province, "")
        self.assertEqual(foo.utc_offset, 0)
        self.assertEqual(foo.site_urls, "http://www.example.com/foo/bar")

        bar = Plot.objects.get(name="The name of the plot", site__site_id="YYYYYYY")
        self.assertIsNotNone(bar)

        bar.name = "Plot the of name the"
        bar.save()
        foo = Site.objects.get(site_id="YYYYYYY")
        self.assertIsNotNone(foo)

        self.assertEqual(bar.site.site_id, 'YYYYYYY')
        self.assertEqual(bar.name, 'Plot the of name the')
        self.assertEqual(bar.description, "Lorem ipsum dolor sit amet, eu eum ludus deleniti, "
                                          "agam scriptorem ex pri, in vide definitiones vis."
                                          " Mea ut ornatus alienum periculis. Eos noster dolorum "
                                          "liberavisse an. Quo dicam graeci aperiri an, te omnes assentior "
                                          "neglegentur eam, has et choro appetere voluptatibus. An ius vocibus "
                                          "recusabo, ridens abhorreant interpretaris per ei. Ne dicant vituperatoribus "
                                          "vel, autem nullam persius te eum, cu augue oratio copiosae mel. Per ea "
                                          "vero utamur, sed no cetero eligendi honestatis.")
        self.assertEqual(bar.location_kmz_url, "http://www.example.com/foo/bar")
        self.assertEqual(bar.size, "5x5")

    def test_list_sites(self):
        """Assert that all Sites were found"""
        objects = Site.objects.all()
        self.assertEqual(len(objects), 2)

    def test_list_plots(self):
        """Assert that all Plots were found"""
        objects = Plot.objects.all()
        self.assertEqual(len(objects), 2)
