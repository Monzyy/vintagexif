from datetime import datetime
from pathlib import Path

import pytest

from vintagexif import get_image_date_mapping

FIXTURE_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture()
def empty_dir() -> Path:
    return FIXTURE_DIR / "empty_dir"


def test_empty_dir_returns_empty_map(empty_dir):
    assert get_image_date_mapping(source_dir=empty_dir) == {}


@pytest.fixture()
def only_year_dir() -> Path:
    return FIXTURE_DIR / "only_year_dir"


def test_should_get_image_date_map_for_dir_with_year(only_year_dir):
    assert get_image_date_mapping(only_year_dir) == {
        only_year_dir / "1995" / "vintage.jpg": datetime(year=1995, month=1, day=1)
    }


@pytest.fixture()
def year_month_dir() -> Path:
    return FIXTURE_DIR / "year_month_dir"


def test_should_get_image_date_map_for_year_month_dir(year_month_dir):
    assert get_image_date_mapping(year_month_dir) == {
        year_month_dir
        / "1994"
        / "02"
        / "vintage.jpg": datetime(year=1994, month=2, day=1)
    }


@pytest.fixture()
def year_month_day_dir() -> Path:
    return FIXTURE_DIR / "year_month_day_dir"


def test_assert_should_get_image_date_map_for_year_month_day_dir(year_month_day_dir):
    assert get_image_date_mapping(year_month_day_dir) == {
        year_month_day_dir
        / "1993"
        / "03"
        / "21"
        / "vintage.jpg": datetime(year=1993, month=3, day=21)
    }
