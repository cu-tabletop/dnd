from ninja import Schema


class RegisterRequest(Schema):
    telegram_id: int
