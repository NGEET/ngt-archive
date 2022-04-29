from django.conf.urls import re_path
from django.contrib.auth.decorators import login_required

from ui.views import IndexView

urlpatterns = [
    re_path(r'^$', login_required(IndexView.as_view()), name="home"),
]
