from functools import partial

from ninja import NinjaAPI

from my_app import error_handlers

api = NinjaAPI()

api.add_router("/", "dnd.urls.dnd_api")


for exception, handler in error_handlers.exception_handlers:
    api.add_exception_handler(exception, partial(handler, router=api))
