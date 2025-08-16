from django.db import models

class File(models.Model):
    filename = models.CharField(max_length=255)
    is_public = models.BooleanField(default=True)

    def __str__(self):
        return self.filename