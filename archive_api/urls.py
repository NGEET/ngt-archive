from django.conf.urls import url, include
from rest_framework import routers
from django.contrib import admin

admin.autodiscover()

from archive_api.viewsets import DataSetViewSet

router = routers.DefaultRouter()
router.register(r'datasets', DataSetViewSet, base_name='dataset')

urlpatterns = [
    url(r'^v1/', include(router.urls, namespace='v1')),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]
