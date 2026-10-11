import datetime
from pathlib import Path
from typing import List

import exiftool
import pytest

import vintagexif

EXIF_DATE_FORMAT = "%Y:%m:%d "
EXIFTOOL_READ_ARGS = ["-G1", "-n"]
EXIFTOOL_READ_PARAMS = ["-a"]
EXIFTOOL_SOURCE_FILE_KEY = "SourceFile"
VIDEO_CONTENT_DATE_TAGS = (
    "ItemList:ContentCreateDate",
    "UserData:ContentCreateDate",
    "Keys:CreationDate",
)
VIDEO_HEADER_DATE_TAGS = (
    "CreateDate",
    "ModifyDate",
    "TrackCreateDate",
    "TrackModifyDate",
    "MediaCreateDate",
    "MediaModifyDate",
)
TEST_TIMEZONES = ("UTC", "Europe/Copenhagen", "America/Los_Angeles")


@pytest.fixture(name="local_timezone", params=TEST_TIMEZONES)
def _set_local_timezone(
    request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("TZ", request.param)


def _read_video_tag_values(video: Path, tag: str) -> List[str]:
    with exiftool.ExifToolHelper(common_args=EXIFTOOL_READ_ARGS) as et:
        metadata = et.get_tags(str(video), tag, params=EXIFTOOL_READ_PARAMS)[0]
    return [value for key, value in metadata.items() if key != EXIFTOOL_SOURCE_FILE_KEY]


def _format_video_date(date: datetime.datetime) -> str:
    return date.strftime(EXIF_DATE_FORMAT) + date.timetz().isoformat(timespec="seconds")


@pytest.mark.parametrize("tag", VIDEO_CONTENT_DATE_TAGS)
def test_should_replace_stale_video_dates(mp4_with_stale_dates: Path, tag: str) -> None:
    date = datetime.datetime(1997, 9, 28)
    expected_dates = [_format_video_date(date.replace(tzinfo=datetime.timezone.utc))]

    vintagexif.set_media_original_date(mp4_with_stale_dates, date)

    actual_dates = _read_video_tag_values(mp4_with_stale_dates, tag)
    assert actual_dates == expected_dates


@pytest.mark.usefixtures("local_timezone")
@pytest.mark.parametrize("header_date_tag", VIDEO_HEADER_DATE_TAGS)
def test_should_treat_naive_video_dates_as_utc(
    mp4_file: Path, header_date_tag: str
) -> None:
    date = datetime.datetime(1997, 9, 28, 0, 0, 1)
    expected_dates = {_format_video_date(date)}

    vintagexif.set_media_original_date(mp4_file, date)

    actual_dates = set(_read_video_tag_values(mp4_file, header_date_tag))
    assert actual_dates == expected_dates


@pytest.mark.usefixtures("local_timezone")
@pytest.mark.parametrize("header_date_tag", VIDEO_HEADER_DATE_TAGS)
def test_should_convert_video_header_dates_to_utc(
    mp4_file: Path, header_date_tag: str
) -> None:
    date = datetime.datetime(
        1997, 9, 28, 0, 0, 1, tzinfo=datetime.timezone(datetime.timedelta(hours=2))
    )
    utc_date = date.astimezone(datetime.timezone.utc).replace(tzinfo=None)
    expected_dates = {_format_video_date(utc_date)}

    vintagexif.set_media_original_date(mp4_file, date)

    actual_dates = set(_read_video_tag_values(mp4_file, header_date_tag))
    assert actual_dates == expected_dates


@pytest.mark.parametrize("tag", VIDEO_CONTENT_DATE_TAGS)
def test_should_preserve_video_timezone_offset(
    mp4_with_stale_dates: Path, tag: str
) -> None:
    date = datetime.datetime(
        1997, 9, 28, tzinfo=datetime.timezone(datetime.timedelta(hours=2))
    )
    expected_dates = [_format_video_date(date)]

    vintagexif.set_media_original_date(mp4_with_stale_dates, date)

    actual_dates = _read_video_tag_values(mp4_with_stale_dates, tag)
    assert actual_dates == expected_dates


def test_should_update_video_date_without_creating_exiftool_backup(
    mp4_file: Path,
) -> None:
    date = datetime.datetime(1997, 9, 28)
    expected_files = {mp4_file}

    vintagexif.set_media_original_date(mp4_file, date)

    actual_files = set(mp4_file.parent.iterdir())
    assert actual_files == expected_files
