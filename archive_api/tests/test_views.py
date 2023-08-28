from django.contrib.auth.models import User
from django.test import TestCase
from django.test import Client
from django.urls import reverse

HTML_METRICS_PUBLIC = """<table>
            <tbody>
            <tr>
                <td colspan="4"><h4 class="title">Datasets</h4></td>
            </tr>
            
                <tr>
                    <td></td>
                    <td>
                        <h5 class="title">Approved</h5></td>
                    <td style="text-align: right">0</td>
                    <td></td>
                </tr>
            
                <tr>
                    <td></td>
                    <td>
                        <h5 class="title">DOIs issued</h5></td>
                    <td style="text-align: right">0</td>
                    <td></td>
                </tr>
            

            <tr>
                <td colspan="4"><h4 class="title">Users</h4></td>
            </tr>
            
                <tr>
                    <td></td>
                    <td>
                        <h5 class="title">Registered</h5></td>
                    <td style="text-align: right">8</td>
                    <td></td>
                </tr>
            
                <tr>
                    <td></td>
                    <td>
                        <h5 class="title">Data Downloads</h5></td>
                    <td style="text-align: right">0</td>
                    <td></td>
                </tr>
            

            </tbody>

        </table>"""

HTML_METRICS_ADMIN = """<table>
                <tbody>
                <tr>
                    <td colspan="4"><h4 class="title">Datasets</h4></td>
                </tr>
                
                    <tr>
                        <td></td>
                        <td>
                            <h5 class="title">Created</h5></td>
                        <td style="text-align: right">4</td>
                        <td></td>
                    </tr>
                
                    <tr>
                        <td></td>
                        <td>
                            <h5 class="title">Submitted</h5></td>
                        <td style="text-align: right">2</td>
                        <td></td>
                    </tr>
                
                    <tr>
                        <td></td>
                        <td>
                            <h5 class="title">Approved</h5></td>
                        <td style="text-align: right">1</td>
                        <td></td>
                    </tr>
                
                    <tr>
                        <td></td>
                        <td>
                            <h5 class="title">Private access</h5></td>
                        <td style="text-align: right">2</td>
                        <td></td>
                    </tr>
                
                    <tr>
                        <td></td>
                        <td>
                            <h5 class="title">DOIs issued</h5></td>
                        <td style="text-align: right">2</td>
                        <td></td>
                    </tr>
                

                <tr>
                    <td colspan="4"><h4 class="title">Users</h4></td>
                </tr>
                
                    <tr>
                        <td></td>
                        <td>
                            <h5 class="title">Registered</h5></td>
                        <td style="text-align: right">8</td>
                        <td></td>
                    </tr>
                
                    <tr>
                        <td></td>
                        <td>
                            <h5 class="title">Data Downloads</h5></td>
                        <td style="text-align: right">0</td>
                        <td></td>
                    </tr>
                

                </tbody>

            </table>"""

HTML_FILTER_START_DATE = """<input type="text" name="start_date" value="2016-01-01" maxlength="10" required id="id_start_date">"""
HTML_BUTTON_DOWNLOAD = """<input class="button left" type="submit" name="download" value="Download Metrics">"""


class MetricsPageTestCase(TestCase):
    fixtures = ['test_auth.json', 'test_archive_api.json']

    def login(self, username):
        client = Client()
        user = User.objects.get(username=username)
        client.force_login(user)
        return client

    def test_search_success(self):
        """Test search success"""

        client = self.login("superadmin")
        response = client.post(reverse("metrics"), data={"start_date": "2016-01-01",
                                                         "end_date": "2021-01-01"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "text/html; charset=utf-8")
        self.assertInHTML(HTML_METRICS_ADMIN, response.content.decode())
        self.assertInHTML(HTML_FILTER_START_DATE, response.content.decode())

    def test_search_fail(self):
        """Test bad search params"""

        client = self.login("superadmin")
        response = client.post(reverse("metrics"), data={"start_date": "2016llksjdfsldkfj",
                                                         "end_date": "2021-01-01"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "text/html; charset=utf-8")
        self.assertInHTML('<ul class="errorlist"><li>Enter a valid date.</li></ul>', response.content.decode())
        self.assertInHTML("<td>Sorry, no metrics.</td>", response.content.decode())

    def test_download(self):
        """Test the the file is downloaded"""

        client = self.login("superadmin")
        response = client.post(reverse("metrics"), data={"download": "Download", "start_date": "2016-01-01",
                                                         "end_date": "2021-01-01"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "text/csv")

        # Using assertInHTML because it is more forgiving.
        self.assertInHTML("""NGT ID,Access Level,Title,Approval Date,Contact,Authors,DOI,Downloads,Citation
NGT0002,Private,Data Set 3,2016-10-29 19:15:35.013361+00:00,"Cage, Luke - POWER",Cage L,https://doi.org/10.15486/ngt/8343947,0,Cage L (2016): Data Set 3. 0.0. NGEE Tropics Data Collection. (dataset). https://doi.org/10.15486/ngt/8343947
NGT0000,Public,Data Set 1,,"Cage, Luke - POWER",,,0,Citation information not available currently. Contact dataset author(s) for citation or acknowledgement text.
NGT0001,Private,Data Set 2,,"Cage, Luke - POWER",Cage L,https://dx.doi.org/10.1111/892375dkfnsi,0,Cage L (2016): Data Set 2. 0.0. NGEE Tropics Data Collection. (dataset). https://dx.doi.org/10.1111/892375dkfnsi
NGT0003,Private,Data Set 4,,"Cage, Luke - POWER",,,0,Citation information not available currently. Contact dataset author(s) for citation or acknowledgement text.
        """, response.content.decode())

    def test_unauthenticated(self):
        """Test unauthenticated user"""
        response = self.check_all_view(Client())
        self.assertNotIn(HTML_BUTTON_DOWNLOAD, response.content.decode())
        self.assertInHTML(HTML_METRICS_PUBLIC, response.content.decode())

    def test_auser(self):
        """Test Metrics page for an regular team user"""

        client = self.login("auser")
        response = self.check_all_login_view(client)
        self.assertInHTML(HTML_METRICS_PUBLIC, response.content.decode())

    def test_admin(self):
        """Test that the metrics page is deplayed"""
        client = self.login("admin")
        response = self.check_all_login_view(client)
        print(response.content.decode())
        self.assertInHTML(HTML_METRICS_ADMIN, response.content.decode())

    def test_staff_access(self):
        """Test that a user marked as staff has access to the Metrics page"""

        client = self.login("superadmin")
        response = self.check_all_login_view(client)
        self.assertInHTML(HTML_METRICS_ADMIN, response.content.decode())

    def check_all_view(self, client):
        """Check what all users unauthenticated and authenticated should view"""

        response = client.get(reverse("metrics"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "text/html; charset=utf-8")
        self.assertInHTML(HTML_FILTER_START_DATE, response.content.decode())
        return response

    def check_all_login_view(self, client):
        """
        Helper methoc to check items that should appear for all logged in users

        :param client:
        :return:
        """
        response = self.check_all_view(client)
        self.assertInHTML(HTML_BUTTON_DOWNLOAD, response.content.decode())
        return response
