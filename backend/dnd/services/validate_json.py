import json


def validate_json(text: str) -> bool:
    try:
        json.loads(text)
        return True
    except (ValueError, json.JSONDecodeError):
        return False


def try_load_json(text: str) -> (dict | None, bool):
    try:
        ret = json.loads(text.replace("\\", ""))
        return ret, True
    except (ValueError, json.JSONDecodeError):
        return None, False
