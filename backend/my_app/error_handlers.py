import logging
from http import HTTPStatus as status

import django.core.exceptions
import pydantic_core
from django.http import Http404, HttpRequest, HttpResponse
from ninja import NinjaAPI
from ninja import errors as ninja_errors

from dnd.schemas import error as error_schemas
from my_app import errors as dnd_errors

logger = logging.getLogger("django")


def handle_django_validation_error(
    request: HttpRequest,
    exc: django.core.exceptions.ValidationError,
    router: NinjaAPI,
) -> HttpResponse:
    logger.exception(exc)

    return router.create_response(
        request,
        error_schemas.ValidationError(message=exc),
        status=status.BAD_REQUEST,
    )


def handle_ninja_validation_error(
    request: HttpRequest,
    exc: ninja_errors.ValidationError,
    router: NinjaAPI,
) -> HttpResponse:
    logger.exception(exc)
    return router.create_response(
        request,
        error_schemas.ValidationError(message=exc.errors),
        status=status.BAD_REQUEST,
    )


def handle_pydantic_validation_error(
    request: HttpRequest,
    exc: pydantic_core.ValidationError,
    router: NinjaAPI,
) -> HttpResponse:
    logger.exception(exc)
    return router.create_response(
        request,
        error_schemas.ValidationError(),
        status=status.BAD_REQUEST,
    )


def handle_django_forbidden_error(
    request: HttpRequest,
    exc: dnd_errors.ForbiddenError,
    router: NinjaAPI,
) -> HttpResponse:
    return router.create_response(
        request,
        error_schemas.ForbiddenError(),
        status=status.FORBIDDEN,
    )


def handle_django_not_found_error(
    request: HttpRequest,
    exc: Http404,
    router: NinjaAPI,
) -> HttpResponse:
    return router.create_response(
        request,
        error_schemas.NotFoundError(),
        status=status.NOT_FOUND,
    )


exception_handlers = [
    (django.core.exceptions.ValidationError, handle_django_validation_error),
    (ninja_errors.ValidationError, handle_ninja_validation_error),
    (pydantic_core.ValidationError, handle_pydantic_validation_error),
    (dnd_errors.ForbiddenError, handle_django_forbidden_error),
    (Http404, handle_django_not_found_error),
]
