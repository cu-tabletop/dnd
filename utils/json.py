import json
from typing import Any, TypeVar
from uuid import UUID

from pydantic import BaseModel

T = TypeVar("T")


def _pydantic_object_hook(obj: Any) -> Any:
    """Hook to convert UUID dicts back to UUID objects in Pydantic model output."""
    if isinstance(obj, dict) and "__uuid__" in obj:
        return UUID(obj["__uuid__"])
    return obj


class JSONEncoder(json.JSONEncoder):
    """JSON encoder that supports UUID and Pydantic models."""

    def default(self, obj: Any):
        if isinstance(obj, BaseModel):
            json_str = obj.model_dump_json()
            return json.loads(json_str, object_hook=_pydantic_object_hook)

        if isinstance(obj, UUID):
            return {"__uuid__": str(obj)}

        if hasattr(obj, "__get_pydantic_core_schema__"):
            return str(obj)

        return super().default(obj)


def json_loads[T](data: str, model_type: type[T] | None = None) -> T | Any:
    """JSON loader that restores UUIDs and optionally validates with Pydantic model."""

    def object_hook(obj: Any) -> Any:
        if isinstance(obj, dict) and "__uuid__" in obj:
            return UUID(obj["__uuid__"])
        return obj

    parsed = json.loads(data, object_hook=object_hook)

    if model_type and issubclass(model_type, BaseModel):
        return model_type.model_validate(parsed)

    return parsed


def json_dumps(obj: Any, **kwargs) -> str:
    """JSON dumper that serializes UUIDs and Pydantic models."""
    if isinstance(obj, BaseModel):
        return obj.model_dump_json(**kwargs)

    return json.dumps(obj, cls=JSONEncoder, **kwargs)


def json_dumps_v2(obj: Any, **kwargs) -> str:
    """Enhanced JSON dumper with better Pydantic integration."""

    def process_value(value: Any) -> Any:
        if isinstance(value, BaseModel):
            return process_value(value.model_dump(mode="json"))
        if isinstance(value, UUID):
            return {"__uuid__": str(value)}
        if isinstance(value, dict):
            return {k: process_value(v) for k, v in value.items()}
        if isinstance(value, list):
            return [process_value(item) for item in value]
        return value

    processed = process_value(obj)

    return json.dumps(processed, cls=JSONEncoder, **kwargs)
