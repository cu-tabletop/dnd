from django.db import models


class Campaign(models.Model):
    title = models.CharField(max_length=255)
    description = models.CharField(max_length=1023, default="")
    icon = models.CharField(max_length=1023, default="")
    # icon = models.ImageField(upload_to="campaign_icons")
    verified = models.BooleanField(default=0)
    private = models.BooleanField(default=0)

    class Config:
        orm_mode = True
