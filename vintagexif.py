import argparse
import datetime
import os
import re
import shutil
from enum import Enum
from pathlib import Path
from typing import Mapping, Optional, List, Callable, Dict, Sequence

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
CLI_PROGRAM_NAME = "vintagexif"
CLI_FAILURE_EXIT_CODE = 1
CLI_INTERRUPTED_EXIT_CODE = 130


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
    """Keep date reads aligned with the metadata fields used by Memories."""
    media_type = _get_image_type(Path(media_path))

    return MEDIA_TYPE_TO_ORIGINAL_DATE_GETTER[media_type](media_path)


def _get_image_type(media_path: Path) -> MediaType:
    try:
        piexif.load(str(media_path))
        return MediaType.Image
    except ValueError:
        return MediaType.Video


def set_media_original_date(media_path: Path, date: datetime.datetime) -> None:
    """Keep QuickTime text and binary timestamps consistent across timezones."""
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
    source_file: Path, date: datetime.datetime, counter: Optional[int]
) -> str:
    match = re.fullmatch(r"\d{4}-\d{2}-\d{2}(.*)", source_file.stem)
    label = match.group(1) if match else ""
    label = re.sub(r"_\d+(?=_|$)", "", label, count=1)
    sequence = f"_{counter:03}" if counter is not None else ""

    return f"{date.strftime('%Y-%m-%d')}{sequence}{label}{source_file.suffix}"


def vintagexif(source_dir: Path, destination_dir: Path) -> List[Path]:
    if not source_dir.is_dir():
        raise ValueError("source_dir is not a directory")
    if not destination_dir.exists():
        destination_dir.mkdir(parents=True, exist_ok=True)
    if not destination_dir.is_dir():
        raise ValueError("destination_dir is not a directory")

    image_date_mapping = get_image_date_mapping(source_dir)
    file_count_by_date: Dict[datetime.datetime, int] = {}
    for date in image_date_mapping.values():
        file_count_by_date[date] = file_count_by_date.get(date, 0) + 1

    last_date = None
    same_date_counter = 0

    destination_files = []

    for file, date in sorted(
        image_date_mapping.items(), key=lambda item: (item[1], item[0])
    ):
        if last_date != date:
            same_date_counter = 1
        else:
            same_date_counter += 1
        counter = same_date_counter
        if file_count_by_date[date] == 1:
            counter = None
        destination_file = destination_dir / destination_file_name_format(
            source_file=file, date=date, counter=counter
        )
        shutil.copy2(file, destination_file)

        set_media_original_date(
            media_path=destination_file,
            date=date + datetime.timedelta(seconds=same_date_counter - 1),
        )

        last_date = date
        destination_files.append(destination_file)

    return destination_files


def _build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=CLI_PROGRAM_NAME,
        description=(
            "Copy photos and videos into dated files, setting recording dates "
            "from filenames or year/month/day folders."
        ),
        epilog=(
            "Video dates without a timezone use UTC. ExifTool must be on PATH "
            "to process videos. Files without an inferred date are skipped."
        ),
    )
    parser.add_argument(
        "source",
        metavar="SOURCE",
        type=Path,
        help="source directory to search recursively",
    )
    parser.add_argument(
        "destination",
        metavar="DESTINATION",
        type=Path,
        help="new or empty output directory outside SOURCE (created if needed)",
    )
    return parser


def _validate_cli_destination(source: Path, destination: Path) -> None:
    if destination == source or source in destination.parents:
        raise ValueError("destination must be outside the source directory")
    if destination.is_dir() and any(destination.iterdir()):
        raise ValueError(
            "destination directory must be empty; choose a new directory "
            "to avoid overwriting existing files"
        )


def main(argv: Optional[Sequence[str]] = None) -> None:
    parser = _build_argument_parser()
    arguments = parser.parse_args(argv)
    try:
        source = arguments.source.expanduser().resolve()
        destination = arguments.destination.expanduser().resolve()
        _validate_cli_destination(source, destination)
        destination_files = vintagexif(source, destination)
    except exiftool.exceptions.ExifToolExecuteError as error:
        parser.exit(
            CLI_FAILURE_EXIT_CODE,
            f"{parser.prog}: error: {error.stderr.strip()}\n",
        )
    except (OSError, ValueError, piexif.InvalidImageDataError) as error:
        parser.exit(CLI_FAILURE_EXIT_CODE, f"{parser.prog}: error: {error}\n")
    except KeyboardInterrupt:
        parser.exit(CLI_INTERRUPTED_EXIT_CODE, f"{parser.prog}: interrupted\n")

    if destination_files:
        print(f"Processed {len(destination_files)} files into {destination}")
    else:
        print(f"No dated media files found in {source}")


if __name__ == "__main__":
    main()
