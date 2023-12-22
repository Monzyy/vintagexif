import os
from datetime import datetime
from pathlib import Path
from typing import Mapping, Optional


def get_image_date_mapping(source_dir: Path) -> Mapping[Path, datetime]:
    map = {}

    for root, dirs, files in os.walk(source_dir):
        root = Path(root)
        year, month, day = None, 1, 1
        if not len(files):
            continue

        root_value = try_parse_date(root.name)
        if root_value is None:
            continue

        parent_value = try_parse_date(root.parent.name)
        if parent_value is not None:
            year = parent_value
            month = root_value
        else:
            year = root_value

        for file in files:
            map[root / file] = datetime(year=year, month=month, day=day)

    return map


def try_parse_date(date: str) -> Optional[int]:
    try:
        value = int(date)
    except ValueError:
        return None
    return value
