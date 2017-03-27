from django.conf.urls import include, url
from django.contrib import admin
from scheduler import views as scheduler_views

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', scheduler_views.home, name='home'),
    url(r'^create_event/', scheduler_views.create_event, name='create_event'),
    url(r'^query_event/', scheduler_views.query_event, name='query_event'),
    url(r'^delete_event/', scheduler_views.delete_event, name='delete_event'),
]
