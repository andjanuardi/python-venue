import json
import os
from datetime import datetime
from typing import List

from config.settings import settings


def export_matches(matches: list, filename: str = None):
    path = os.path.join(settings.DATA_DIR, filename or f"matches_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json")
    data = []
    for m in matches:
        if hasattr(m, 'model_dump'):
            data.append(m.model_dump(mode="json"))
        elif isinstance(m, dict):
            data.append(m)
        else:
            data.append(m.__dict__)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return path


def export_streams(streams: list, filename: str = None):
    path = os.path.join(settings.DATA_DIR, filename or f"streams_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json")
    data = []
    for s in streams:
        if hasattr(s, 'model_dump'):
            data.append(s.model_dump(mode="json"))
        elif isinstance(s, dict):
            data.append(s)
        else:
            data.append(s.__dict__)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return path
