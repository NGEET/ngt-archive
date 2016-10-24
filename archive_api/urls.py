from django.conf.urls import url, include
from django.contrib import admin
from rest_framework import routers

admin.autodiscover()

from archive_api.viewsets import DataSetViewSet, MeasurementVariableViewSet, SiteViewSet, ContactViewSet, PlotViewSet

router = routers.DefaultRouter()
router.register(r'datasets', DataSetViewSet, base_name='dataset')
router.register(r'sites', SiteViewSet, base_name='site')
router.register(r'variables', MeasurementVariableViewSet, base_name='measurementvariable')
router.register(r'contacts', ContactViewSet, base_name='contact')
router.register(r'plots', PlotViewSet, base_name='plot')

urlpatterns = [
    url(r'^v1/', include(router.urls, namespace='v1')),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]
