import json

from django.core.files.base import ContentFile
from django.db import models

from dnd.models.campaign import Campaign
from dnd.models.player import Player


class Character(models.Model):
    id = models.AutoField(auto_created=True, primary_key=True)
    owner = models.ForeignKey(
        Player,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    campaign = models.ForeignKey(Campaign, models.CASCADE, null=True)

    data = models.FileField(upload_to="chardata")

    def load_data(self):
        """Internal function that loads data from file stored in database."""
        with self.data.open("r") as f:
            return json.load(f)

    def save_data(self, data: dict):
        """Internal function that saves data to a file stored in database."""
        self.data.save(
            f"{self.id}.json", ContentFile(json.dumps(data)), save=False
        )

    def get(self, *args):
        """
        Gets specific parameter from character data.
        Usage: Put path to the param into args
        """
        cur = self.load_data()
        for arg in args:
            try:
                cur = cur[arg]
            except (KeyError, IndexError, TypeError):
                return None
        return cur

    def set(self, *args, **kwargs) -> bool:
        """
        Sets specific parameter(-s) in character data to a value
        Usage: Put path to the param into args and what should we change to kwargs
        Returns True if set successfully and False if path not found
        Example usage:
        char_obj.set("info", "charClass", value="Колдун")
        """
        data = self.load_data()
        cur = data
        for arg in args:
            try:
                cur = cur[arg]
            except (KeyError, IndexError, TypeError):
                return False
        for n, v in kwargs:
            cur[n] = v
        self.save_data(data)
        return True
