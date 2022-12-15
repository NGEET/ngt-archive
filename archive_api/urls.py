from django.conf.urls import include
from django.contrib import admin
from django.urls import re_path
from rest_framework import routers

from archive_api.views import metrics_datasets

admin.autodiscover()

from archive_api.viewsets import DataSetViewSet, MeasurementVariableViewSet, SiteViewSet, PersonViewSet, PlotViewSet

router = routers.DefaultRouter()
router.register(r'datasets', DataSetViewSet, basename='dataset')
router.register(r'sites', SiteViewSet, basename='site')
router.register(r'variables', MeasurementVariableViewSet, basename='measurementvariable')
router.register(r'people', PersonViewSet, basename='person')
router.register(r'plots', PlotViewSet, basename='plot')

urlpatterns = [
    re_path(r'^v1/', include((router.urls, 'archive_api'), namespace='v1')),
    re_path(r'^metrics/', metrics_datasets, name='metrics'),
    re_path(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]
