import datetime
import os
import shutil
from pathlib import Path
from typing import Mapping, Optional, List

import exif
import piexif


# def get_image_original_date(image_path: Path) -> Optional[datetime.datetime]:
#    with image_path.open("rb") as image_file:
#        image = exif.Image(image_file)
#    datetime_original = image.get("datetime_original")
#    if datetime_original is None:
#        return None
#    return datetime.datetime.strptime(datetime_original, "%Y:%m:%d %H:%M:%S")


def get_image_original_date(image_path: Path) -> Optional[datetime.datetime]:
    exif_dict = piexif.load(str(image_path))
    date_string = exif_dict.get("Exif", {}).get(piexif.ExifIFD.DateTimeOriginal)
    if date_string is None:
        return None
    return datetime.datetime.strptime(date_string.decode("utf8"), "%Y:%m:%d %H:%M:%S")


# def set_image_original_date(image_path: Path, date: datetime.datetime):
#    with image_path.open("rb") as image_file:
#        image = exif.Image(image_file)
#
#    image.datetime_original = datetime.datetime.strftime(date, exif.DATETIME_STR_FORMAT)
#
#    with image_path.open("wb") as image_file:
#        image_file.write(image.get_file())


def set_image_original_date(image_path: Path, date: datetime.datetime):
    exif_dict = piexif.load(str(image_path))

    exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = datetime.datetime.strftime(
        date, "%Y:%m:%d %H:%M:%S"
    )
    exif_bytes = piexif.dump(exif_dict)
    piexif.insert(exif_bytes, str(image_path))


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

    for file, date in sorted(image_date_mapping.items(), key=lambda p: p[1]):
        if last_date != date:
            counter = 1
        else:
            counter += 1
        destination_file = (
            destination_dir / f"{date.strftime('%Y-%m-%d')}_{counter:03}{file.suffix}"
        )
        shutil.copy2(file, destination_file)
        set_image_original_date(destination_file, date)

        last_date = date
        destination_files.append(destination_file)

    return destination_files


if __name__ == "__main__":

    def _m():
        vintagexif(
            Path("/mnt/d/NextCloud/Familie-mappen/Scans"), Path("/mnt/d/vintagexif")
        )

    _m()
