import csv
import os
from datetime import datetime
from typing import List

from config.settings import settings


def export_matches_csv(matches: list, filename: str = None):
    path = os.path.join(settings.DATA_DIR, filename or f"matches_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv")
    if not matches:
        return path

    # Get field names from first item
    first = matches[0]
    if hasattr(first, 'model_dump'):
        fields = list(first.model_dump().keys())
    elif isinstance(first, dict):
        fields = list(first.keys())
    else:
        fields = list(first.__dict__.keys())

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for m in matches:
            if hasattr(m, 'model_dump'):
                writer.writerow(m.model_dump(mode="json"))
            elif isinstance(m, dict):
                writer.writerow(m)
            else:
                writer.writerow(m.__dict__)
    return path


def export_streams_csv(streams: list, filename: str = None):
    path = os.path.join(settings.DATA_DIR, filename or f"streams_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv")
    if not streams:
        return path

    first = streams[0]
    if hasattr(first, 'model_dump'):
        fields = list(first.model_dump().keys())
    elif isinstance(first, dict):
        fields = list(first.keys())
    else:
        fields = list(first.__dict__.keys())

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for s in streams:
            if hasattr(s, 'model_dump'):
                writer.writerow(s.model_dump(mode="json"))
            elif isinstance(s, dict):
                writer.writerow(s)
            else:
                writer.writerow(s.__dict__)
    return path
