import shutil
from pathlib import Path

import pytest

FIXTURE_DIR = Path(__file__).parent / "fixtures"


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


@pytest.fixture()
def destination_dir() -> Path:
    dest_dir = FIXTURE_DIR / "destination"
    yield dest_dir
    shutil.rmtree(dest_dir, ignore_errors=True)


@pytest.fixture
def two_images_same_date_dir() -> Path:
    return FIXTURE_DIR / "two_images"


@pytest.fixture
def flat_structured_image_dir() -> Path:
    return FIXTURE_DIR / "flat_structure"


@pytest.fixture
def mp4_dir() -> Path:
    return FIXTURE_DIR / "mp4"


@pytest.fixture
def appended_label_dir() -> Path:
    return FIXTURE_DIR / "appended_label"


@pytest.fixture
def multiple_appended_labels_dir() -> Path:
    return FIXTURE_DIR / "multiple_appended_labels"
