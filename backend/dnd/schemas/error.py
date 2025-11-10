from ninja import Schema


class BaseError(Schema):
    message: str


class ValidationError(BaseError):
    message: str | dict | list = "Ошибка в данных запроса."


class ForbiddenError(BaseError):
    message: str = "Запрещено"


class NotFoundError(BaseError):
    message: str = "Объект не найден"
