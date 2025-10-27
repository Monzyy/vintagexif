import datetime
from pathlib import Path

from vintagexif import get_image_date_mapping


def test_empty_dir_returns_empty_map(empty_dir):
    assert get_image_date_mapping(source_dir=empty_dir) == {}


def test_should_get_image_date_map_for_dir_with_year(only_year_dir):
    assert get_image_date_mapping(only_year_dir) == {
        only_year_dir
        / "1995"
        / "vintage.jpg": datetime.datetime(year=1995, month=1, day=1)
    }


def test_should_get_image_date_map_for_year_month_dir(year_month_dir):
    assert get_image_date_mapping(year_month_dir) == {
        year_month_dir
        / "1994"
        / "02"
        / "vintage.jpg": datetime.datetime(year=1994, month=2, day=1)
    }


def test_should_get_image_date_map_for_year_month_day_dir(year_month_day_dir):
    assert get_image_date_mapping(year_month_day_dir) == {
        year_month_day_dir
        / "1993"
        / "03"
        / "21"
        / "vintage.jpg": datetime.datetime(year=1993, month=3, day=21)
    }


def test_should_get_image_date_map_for_flat_structured_dir(flat_structured_image_dir):
    assert get_image_date_mapping(flat_structured_image_dir) == {
        flat_structured_image_dir
        / "1996-08-27.jpg": datetime.datetime(year=1996, month=8, day=27)
    }
