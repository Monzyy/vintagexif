import datetime
import os
import shutil
from pathlib import Path
from typing import Mapping, Optional, List

import exif


class Image:
    def __init__(self, file_path: Path):
        if not file_path.is_file():
            raise ValueError("File does not exist")

        self._image = exif.Image(file_path.open("rb"))

    def get_original_date(self) -> Optional[datetime.datetime]:
        datetime_original = self._image.get("datetime_original")
        if datetime_original is None:
            return None

        return datetime.datetime.strptime(datetime_original, "%Y:%m:%d %H:%M:%S")

    def set_original_date(self, date: datetime.date):
        self._image.datetime_original = datetime.datetime.strftime(
            date, "%Y:%m:%d %H:%M:%S"
        )


def get_image_date_mapping(source_dir: Path) -> Mapping[Path, datetime.datetime]:
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
        grand_parent_value = try_parse_date(root.parent.parent.name)
        if grand_parent_value is not None and parent_value is not None:
            year = grand_parent_value
            month = parent_value
            day = root_value
        elif parent_value is not None:
            year = parent_value
            month = root_value
        else:
            year = root_value

        for file in files:
            map[root / file] = datetime.datetime(year=year, month=month, day=day)

    return map


def try_parse_date(date: str) -> Optional[int]:
    try:
        value = int(date)
    except ValueError:
        return None
    return value


def vintagexif(source_dir: Path, destination_dir: Path) -> List[Path]:
    if not source_dir.is_dir():
        raise ValueError("source_dir is not a directory")
    if not destination_dir.exists():
        destination_dir.mkdir(exist_ok=True)
    if not destination_dir.is_dir():
        raise ValueError("destination_dir is not a directory")

    image_date_mapping = get_image_date_mapping(source_dir)

    last_date = None
    counter = 1

    destination_files = []
    for file, date in image_date_mapping.items():
        if last_date != date:
            counter = 1
        else:
            counter += 1
        destination_file = (
            destination_dir / f"{date.strftime('%Y-%m-%d')}_{counter:03}{file.suffix}"
        )
        shutil.copy2(file, destination_file)
        dest_image = Image(destination_file)

        last_date = date
        destination_files.append(destination_file)

    return destination_files


if __name__ == "__main__":
    m = get_image_date_mapping(Path("/mnt/d/NextCloud/Familie-mappen/Scans"))
    ...
