from datetime import datetime

from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.status import *


@api_view(["GET"])
def health_view(request: Request) -> Response:
    return Response(
        data={
            "status": "healthy",
            "timestamp": datetime.now().isoformat() + "Z",
        },
        status=HTTP_200_OK,
    )
