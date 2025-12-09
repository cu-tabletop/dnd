from tortoise import fields, models
from tortoise.contrib.postgres.fields import ArrayField
from tortoise.expressions import Q
from tortoise.fields import OnDelete

from db.exceptions import CursedTransferError, ItemHeldByBothError, NoHolderError
from db.models import Character, User
from db.models.base import TimestampedModel, UuidModel


class Item(TimestampedModel, UuidModel):
    title = fields.CharField(max_length=255)
    quantity = fields.IntField(default=1)
    description = fields.TextField(default="")

    # Владелец предмета может быть как персонаж, так и юзер
    holder_character = fields.ForeignKeyField(
        "models.Character", null=True, related_name="inventory_items", on_delete=OnDelete.SET_NULL
    )
    holder_user = fields.ForeignKeyField(
        "models.User", null=True, related_name="user_items", on_delete=OnDelete.SET_NULL
    )
    campaign = fields.ForeignKeyField("models.Campaign", related_name="campaign_items", on_delete=fields.CASCADE)

    # Опциональные поля
    weight = fields.FloatField(null=True)
    value = fields.DecimalField(max_digits=10, decimal_places=2, null=True)
    rarity = fields.CharField(max_length=50, null=True)
    attunement_required = fields.BooleanField(default=False)
    attuned_character = fields.ForeignKeyField(
        "models.Character", null=True, related_name="attuned_items", on_delete=OnDelete.SET_NULL
    )
    tags = ArrayField(element_type="varchar", size=100, null=True)

    is_equipped = fields.BooleanField(default=False)
    equipped_slot = fields.CharField(max_length=50, null=True)
    is_cursed = fields.BooleanField(default=False)
    charges = fields.IntField(null=True)
    current_durability = fields.IntField(null=True)
    max_durability = fields.IntField(null=True)
    magic_bonus = fields.IntField(default=0)
    magical_properties = fields.JSONField(null=True)

    class Meta:
        table = "items"

        constraints = [
            Q(holder_character_id__isnull=False, holder_user_id__isnull=True)
            | Q(holder_character_id__isnull=True, holder_user_id__isnull=False),
        ]
        indexes = [
            models.Index(fields=["title"]),
            models.Index(fields=["rarity"]),
            models.Index(fields=["campaign_id", "holder_character_id"]),
            models.Index(fields=["campaign_id", "holder_user_id"]),
        ]

    def clean(self):
        """Validate model before saving"""
        if self.holder_character and self.holder_user:
            raise ItemHeldByBothError

        if not self.holder_character and not self.holder_user:
            raise NoHolderError

    async def save(self, *args, **kwargs):
        """Override save to include validation"""
        self.clean()
        await super().save(*args, **kwargs)

    @property
    def owner(self):
        """Return the actual owner (character or user)"""
        return self.holder_character or self.holder_user

    @property
    def is_magical(self):
        """Check if item is magical"""
        return self.magic_bonus > 0 or (self.magical_properties and len(self.magical_properties) > 0)

    @property
    def is_broken(self):
        """Check if item is broken"""
        if self.current_durability is not None and self.max_durability is not None:
            return self.current_durability <= 0
        return False

    @property
    def is_attuned(self):
        """Check if item is currently attuned"""
        return self.attuned_character.id is not None

    def get_durability_percentage(self):
        """Get durability as percentage"""
        if self.current_durability is not None and self.max_durability is not None:
            return (self.current_durability / self.max_durability) * 100
        return None

    async def transfer(self, to_character: Character = None, to_user: User = None, *, force: bool = False):
        """Transfer item to another character or user"""
        if to_character and to_user:
            raise ItemHeldByBothError

        if not to_character and not to_user:
            raise NoHolderError

        if self.is_cursed and not force:
            raise CursedTransferError

        # Update holder
        self.holder_character = to_character
        self.holder_user = to_user

        # If equipped, unequip when transferring
        if self.is_equipped:
            self.is_equipped = False
            self.equipped_slot = None

        await self.save()

    async def duplicate(self) -> "Item":
        """Create duplicate of this item"""
        return await Item.create(
            title=self.title,
            quantity=1,
            description=self.description,
            weight=self.weight,
            value=self.value,
            rarity=self.rarity,
            attunement_required=self.attunement_required,
            holder_character=self.holder_character,
            holder_user=self.holder_user,
            campaign=self.campaign,
            magical_properties=self.magical_properties,
            magic_bonus=self.magic_bonus,
            tags=self.tags.copy() if self.tags else None,
        )

    def __str__(self) -> str:
        holder = self.holder_character.name if self.holder_character else self.holder_user.username
        return f"{self.title} (x{self.quantity}) - Held by: {holder}"

    class PydanticMeta:
        exclude = ["campaign"]
