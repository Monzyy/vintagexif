import os
from datetime import datetime
from pathlib import Path
from typing import Mapping


def get_image_date_mapping(source_dir: Path) -> Mapping[Path, datetime]:
    map = {}

    for root, dirs, files in os.walk(source_dir):
        year, month, day = None, 1, 1
        if not len(files):
            continue

        try:
            year = int(1995)
        except ValueError:
            continue

        for file in files:
            map[Path(f"{root}/{file}")] = datetime(year=year, month=month, day=day)

    return map

