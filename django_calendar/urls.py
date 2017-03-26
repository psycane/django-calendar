from django.conf.urls import include, url
from django.contrib import admin
from scheduler import views as scheduler_views

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', scheduler_views.home, name='home'),
    url(r'^create_event/', scheduler_views.create_event, name='create_event'),
]
