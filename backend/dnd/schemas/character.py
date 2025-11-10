from ninja import Schema


class UploadCharacter(Schema):
    owner_id: int
    campaign_id: int
    data: dict


class CharacterOut(Schema):
    id: int
    owner_id: int
    owner_telegram_id: int
    campaign_id: int
    data: dict
