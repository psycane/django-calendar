from django.contrib import admin

# Register your models here.
from .models import Event


class EventAdmin(admin.ModelAdmin):
    list_display = ['id',
                    '__str__',
                    'location',
                    'start_date',
                    'end_date',
                    'description']

    class Meta:
        model = Event


admin.site.register(Event, EventAdmin)
