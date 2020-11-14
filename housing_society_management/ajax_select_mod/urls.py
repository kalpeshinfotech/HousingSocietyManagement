from django.urls import re_path
from . import views

urlpatterns = [
    re_path(r'^ajax_lookup/(?P<channel>[-\w]+)$', views.ajax_lookup,name='ajax_lookup')
]
