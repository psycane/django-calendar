from django.db import models

# Create your models here.


class Event(models.Model):
    event_name = models.CharField(max_length=30)
    location = models.CharField(max_length=30)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    description = models.CharField(max_length=100)

    def __str__(self):
        return self.event_name
