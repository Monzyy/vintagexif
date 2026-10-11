import datetime
from pathlib import Path
from typing import Dict

from vintagexif import get_image_date_mapping


def test_should_return_empty_map_for_empty_dir(empty_dir: Path) -> None:
    expected_dates: Dict[Path, datetime.datetime] = {}

    actual_dates = get_image_date_mapping(source_dir=empty_dir)

    assert actual_dates == expected_dates


def test_should_get_image_date_map_for_dir_with_year(only_year_dir: Path) -> None:
    expected_dates = {
        only_year_dir / "1995" / "vintage.jpg": datetime.datetime(1995, 1, 1)
    }

    actual_dates = get_image_date_mapping(only_year_dir)

    assert actual_dates == expected_dates


def test_should_get_image_date_map_for_year_month_dir(year_month_dir: Path) -> None:
    expected_dates = {
        year_month_dir / "1994" / "02" / "vintage.jpg": datetime.datetime(1994, 2, 1)
    }

    actual_dates = get_image_date_mapping(year_month_dir)

    assert actual_dates == expected_dates


def test_should_get_image_date_map_for_year_month_day_dir(
    year_month_day_dir: Path,
) -> None:
    expected_dates = {
        year_month_day_dir
        / "1993"
        / "03"
        / "21"
        / "vintage.jpg": datetime.datetime(1993, 3, 21)
    }

    actual_dates = get_image_date_mapping(year_month_day_dir)

    assert actual_dates == expected_dates


def test_should_get_image_date_map_for_flat_structured_dir(
    flat_structured_image_dir: Path,
) -> None:
    expected_date = datetime.datetime(1996, 8, 27)
    expected_file = flat_structured_image_dir / f"{expected_date:%Y-%m-%d}.jpg"
    expected_dates = {expected_file: expected_date}

    actual_dates = get_image_date_mapping(flat_structured_image_dir)

    assert actual_dates == expected_dates
