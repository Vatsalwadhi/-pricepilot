import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

def make_json_safe(obj):
    if isinstance(obj, dict):
        return {str(k): make_json_safe(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_json_safe(item) for item in obj]
    elif isinstance(obj, tuple):
        return [make_json_safe(item) for item in obj]
    elif isinstance(obj, set):
        return [make_json_safe(item) for item in obj]
    elif isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    elif isinstance(obj, UUID):
        return str(obj)
    elif isinstance(obj, Enum):
        return make_json_safe(obj.value)
    else:
        return obj
