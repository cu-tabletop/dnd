import enum

from ninja import ModelSchema, Schema

from dnd.models.campaign import Campaign


class CreateCampaignRequest(Schema):
    telegram_id: int
    title: str
    icon: str | None = None
    description: str | None = None


class UpdateCampaignRequest(Schema):
    telegram_id: int
    campaign_id: int
    title: str | None = None
    icon: str | None = None
    description: str | None = None


class CampaignModelSchema(ModelSchema):
    class Meta:
        model = Campaign
        fields = ["id", "title", "description", "icon", "verified", "private"]
        fields_optional = ["icon", "description"]


class AddToCampaignRequest(Schema):
    campaign_id: int
    owner_id: int
    user_id: int


class CampaignPermissions(int, enum.Enum):
    PLAYER = 0
    MASTER = 1
    OWNER = 2


class CampaignEditPermissions(Schema):
    campaign_id: int
    owner_id: int
    user_id: int
    status: CampaignPermissions
