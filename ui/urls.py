
from django.contrib.auth.decorators import login_required
from django.urls import re_path

from ui.views import IndexView

urlpatterns = [
    re_path(r'^$', login_required(IndexView.as_view()), name="home"),
]
