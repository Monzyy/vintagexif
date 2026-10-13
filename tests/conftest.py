import shutil
from pathlib import Path

import exiftool
import pytest

FIXTURE_DIR = Path(__file__).parent / "fixtures"
MP4_FIXTURE_NAME = "1997-09-28.mp4"
STALE_VIDEO_DATES = {
    "ItemList:ContentCreateDate": "2020:01:02 03:04:05+00:00",
    "UserData:ContentCreateDate": "2021:01:02 03:04:05+00:00",
    "Keys:CreationDate": "2022:01:02 03:04:05+00:00",
}
EXIFTOOL_WRITE_PARAMS = ["-overwrite_original"]


@pytest.fixture()
def empty_dir() -> Path:
    return FIXTURE_DIR / "empty_dir"


@pytest.fixture()
def only_year_dir() -> Path:
    return FIXTURE_DIR / "only_year_dir"


@pytest.fixture()
def year_month_dir() -> Path:
    return FIXTURE_DIR / "year_month_dir"


@pytest.fixture()
def year_month_day_dir() -> Path:
    return FIXTURE_DIR / "year_month_day_dir"


@pytest.fixture(name="destination_dir")
def _get_destination_dir(tmp_path: Path) -> Path:
    return tmp_path / "destination"


@pytest.fixture
def two_images_same_date_dir() -> Path:
    return FIXTURE_DIR / "two_images"


@pytest.fixture
def flat_structured_image_dir() -> Path:
    return FIXTURE_DIR / "flat_structure"


@pytest.fixture
def mp4_dir() -> Path:
    return FIXTURE_DIR / "mp4"


@pytest.fixture(name="mp4_file")
def _copy_mp4(mp4_dir: Path, tmp_path: Path) -> Path:
    video = tmp_path / "video.mp4"
    shutil.copyfile(mp4_dir / MP4_FIXTURE_NAME, video)
    return video


@pytest.fixture(name="mp4_with_stale_dates")
def _write_stale_video_dates(mp4_file: Path) -> Path:
    with exiftool.ExifToolHelper() as et:
        et.set_tags(
            str(mp4_file),
            STALE_VIDEO_DATES,
            params=EXIFTOOL_WRITE_PARAMS,
        )
    return mp4_file


@pytest.fixture
def appended_label_dir() -> Path:
    return FIXTURE_DIR / "appended_label"


@pytest.fixture
def multiple_appended_labels_dir() -> Path:
    return FIXTURE_DIR / "multiple_appended_labels"


@pytest.fixture
def numbered_sources_dir() -> Path:
    return FIXTURE_DIR / "numbered_sources"


@pytest.fixture
def short_numbered_videos_dir() -> Path:
    return FIXTURE_DIR / "short_numbered_videos"
