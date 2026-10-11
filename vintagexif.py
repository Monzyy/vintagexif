import datetime
import os
import re
import shutil
from enum import Enum
from pathlib import Path
from typing import Mapping, Optional, List, Callable, Dict

import exiftool
import piexif
from dateutil.parser import parse


EXIF_DATE_FORMAT = "%Y:%m:%d %H:%M:%S"
EXIF_DATE_WITH_OFFSET_FORMAT = EXIF_DATE_FORMAT + "%z"
VIDEO_RECORDING_DATE_TAGS = (
    "QuickTime:ContentCreateDate",
    "QuickTime:CreationDate",
    "QuickTime:CreateDate",
)
VIDEO_WRITABLE_DATE_TAGS = VIDEO_RECORDING_DATE_TAGS + (
    "File:FileModifyDate",
    "QuickTime:ModifyDate",
    "QuickTime:TrackCreateDate",
    "QuickTime:TrackModifyDate",
    "QuickTime:MediaCreateDate",
    "QuickTime:MediaModifyDate",
)
# PyExifTool's default -n bypasses input timezone conversion for QuickTime dates.
EXIFTOOL_DATE_WRITE_ARGS = ["-G"]
EXIFTOOL_DATE_WRITE_PARAMS = ["-api", "QuickTimeUTC=1", "-P", "-overwrite_original"]


class MediaType(Enum):
    Image = "IMAGE"
    Video = "VIDEO"


def _set_image_original_date(date: datetime.datetime, media_path: Path):
    exif_dict = piexif.load(str(media_path))

    exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = datetime.datetime.strftime(
        date, "%Y:%m:%d %H:%M:%S"
    )
    exif_bytes = piexif.dump(exif_dict)
    piexif.insert(exif_bytes, str(media_path))


def _format_video_timestamp(date: datetime.datetime) -> str:
    date_with_offset = (
        date.replace(tzinfo=datetime.timezone.utc) if date.utcoffset() is None else date
    )
    return date_with_offset.strftime(EXIF_DATE_WITH_OFFSET_FORMAT)


def _set_video_original_date(date: datetime.datetime, video_path: Path) -> None:
    timestamp = _format_video_timestamp(date)
    with exiftool.ExifToolHelper(common_args=EXIFTOOL_DATE_WRITE_ARGS) as et:
        et.set_tags(
            files=str(video_path),
            tags=dict.fromkeys(VIDEO_WRITABLE_DATE_TAGS, timestamp),
            params=EXIFTOOL_DATE_WRITE_PARAMS,
        )


MEDIA_TYPE_TO_ORIGINAL_DATE_SETTER: Dict[
    MediaType, Callable[[datetime.datetime, Path], None]
] = {
    MediaType.Image: _set_image_original_date,
    MediaType.Video: _set_video_original_date,
}


def _get_image_original_date(media_path: Path) -> Optional[datetime.datetime]:
    exif_dict = piexif.load(str(media_path))
    date_string = exif_dict.get("Exif", {}).get(piexif.ExifIFD.DateTimeOriginal)
    if date_string is None:
        return None
    return datetime.datetime.strptime(date_string.decode("utf8"), "%Y:%m:%d %H:%M:%S")


def _parse_video_original_date(metadata: Mapping[str, str]) -> datetime.datetime:
    for tag_name in VIDEO_RECORDING_DATE_TAGS:
        if tag_name not in metadata:
            continue
        value = metadata[tag_name]
        try:
            date, time = value.split(" ", maxsplit=1)
            iso_date = date.replace(":", "-")
            return datetime.datetime.fromisoformat(f"{iso_date}T{time}").replace(
                tzinfo=None
            )
        except ValueError as error:
            raise ValueError(
                f"Invalid video recording date in {tag_name}: {value!r}"
            ) from error
    raise ValueError("Video has no embedded recording date")


def _get_video_original_date(media_path: Path) -> datetime.datetime:
    with exiftool.ExifToolHelper() as et:
        metadata = et.get_tags(str(media_path), VIDEO_RECORDING_DATE_TAGS)[0]
    try:
        return _parse_video_original_date(metadata)
    except ValueError as error:
        raise ValueError(f"{media_path}: {error}") from error


MEDIA_TYPE_TO_ORIGINAL_DATE_GETTER: Dict[
    MediaType, Callable[[Path], Optional[datetime.datetime]]
] = {
    MediaType.Image: _get_image_original_date,
    MediaType.Video: _get_video_original_date,
}


def get_media_original_date(media_path: Path) -> Optional[datetime.datetime]:
    media_type = _get_image_type(Path(media_path))

    return MEDIA_TYPE_TO_ORIGINAL_DATE_GETTER[media_type](media_path)


def _get_image_type(media_path: Path) -> MediaType:
    try:
        piexif.load(str(media_path))
        return MediaType.Image
    except ValueError:
        return MediaType.Video


def set_media_original_date(media_path: Path, date: datetime.datetime) -> None:
    media_type = _get_image_type(media_path)

    MEDIA_TYPE_TO_ORIGINAL_DATE_SETTER[media_type](date, media_path)


def get_image_date_mapping(source_dir: Path) -> Mapping[Path, datetime.datetime]:
    map = {}

    for root, dirs, files in os.walk(source_dir):
        root = Path(root)
        year, month, day = None, 1, 1
        dir_has_files = len(files)
        if not dir_has_files:
            continue

        for file in files:
            dt = try_parse_date(Path(file).stem)
            if dt is not None:
                map[root / file] = dt

        root_value = try_parse_int(root.name)
        if root_value is None:
            continue

        parent_value = try_parse_int(root.parent.name)
        grand_parent_value = try_parse_int(root.parent.parent.name)
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


def try_parse_int(date: str) -> Optional[int]:
    try:
        value = int(date)
    except ValueError:
        return None
    return value


def try_parse_date(filename: str) -> Optional[datetime.datetime]:
    match = re.match(
        r"^(\d{1,4})([-_])(\d{1,2})\2(\d{1,2})(?=[^\d]|$)",
        filename,
    )
    if not match:
        return None

    year, _, month, day = match.groups()
    return datetime.datetime(int(year), int(month), int(day))


def destination_file_name_format(
    source_file: Path, date: datetime.datetime, counter: int
) -> str:
    match = re.fullmatch(r"\d{4}-\d{2}-\d{2}(.*)", source_file.stem)
    label = match.group(1) if match else ""

    return f"{date.strftime('%Y-%m-%d')}_{counter:03}{label}{source_file.suffix}"


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
        destination_file = destination_dir / destination_file_name_format(
            source_file=file, date=date, counter=counter
        )
        shutil.copy2(file, destination_file)

        set_media_original_date(
            media_path=destination_file,
            date=date + datetime.timedelta(seconds=counter - 1),
        )

        last_date = date
        destination_files.append(destination_file)

    return destination_files


if __name__ == "__main__":

    def _m():
        vintagexif(
            source_dir=Path("G:\\Sara Hjemmevideor"),
            destination_dir=Path("G:\\vintagexif"),
        )

    _m()
