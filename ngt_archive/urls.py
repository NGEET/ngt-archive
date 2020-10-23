"""ngt_data URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from django.urls import path

from archive_api import urls as api_urls
from ui import urls as ui_urls
from archive_api.views import doi, download, dois
from django.contrib.auth import views as auth_views
import oauth2_provider.views as oauth2_views
from django.contrib.auth.decorators import user_passes_test

admin.site.site_header = 'NGEE Tropics Admin Site'
admin.site.site_title = 'NGEET Administration'


def user_can_create_tokens(user):
    """Only Superusers and NGT Administrators can create oauth applications"""
    return user.is_superuser or user.has_group("NGT Administrator")


# OAuth2 provider endpoints
oauth2_endpoint_views = [
    path('authorize/', oauth2_views.AuthorizationView.as_view(), name="authorize"),
    path('token/', oauth2_views.TokenView.as_view(), name="token"),
    path('revoke-token/', oauth2_views.RevokeTokenView.as_view(), name="revoke-token"),
]


# OAuth2 Application Management endpoints
oauth2_endpoint_views += [
    path('applications/', user_passes_test(user_can_create_tokens)(oauth2_views.ApplicationList.as_view()), name="list"),
    path('applications/register/', user_passes_test(user_can_create_tokens)(oauth2_views.ApplicationRegistration.as_view()), name="register"),
    path('applications/<pk>/', user_passes_test(user_can_create_tokens)(oauth2_views.ApplicationDetail.as_view()), name="detail"),
    path('applications/<pk>/delete/', user_passes_test(user_can_create_tokens)(oauth2_views.ApplicationDelete.as_view()), name="delete"),
    path('applications/<pk>/update/', user_passes_test(user_can_create_tokens)(oauth2_views.ApplicationUpdate.as_view()), name="update"),
]


# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    url(r'^', include(ui_urls)),
    path('o/', include((oauth2_endpoint_views,'oauth2_provider'), namespace='oauth2_provider')),
    url(r'^api/', include(api_urls)),
    url(r'^admin/', admin.site.urls),
    url(r'^dois/(?P<ngt_id>[a-zA-Z0-9]+)/$', doi, name='doi'),
    url(r'^dois/$', dois, name='dois'),
    url(r'^download/(?P<ngt_id>[a-zA-Z0-9]+)', download, name='download'),
    url(r'^login/$', auth_views.LoginView.as_view(template_name='archive_api/login.html'), name='login'),
    url(r'^logout/$', auth_views.LogoutView.as_view(), name='logout'),
]


