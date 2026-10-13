import datetime
from pathlib import Path

import vintagexif


def test_should_copy_image_to_destination(
    year_month_day_dir: Path, destination_dir: Path
) -> None:
    expected_file = destination_dir / "1993-03-21.jpg"

    vintagexif.vintagexif(
        source_dir=year_month_day_dir, destination_dir=destination_dir
    )

    assert expected_file.is_file()


def test_should_append_unique_number_to_images_from_same_date(
    two_images_same_date_dir: Path, destination_dir: Path
) -> None:
    expected_files = {
        destination_dir / "1996-01-01_001.jpg",
        destination_dir / "1996-01-01_002.jpg",
    }

    destination_files = vintagexif.vintagexif(
        source_dir=two_images_same_date_dir, destination_dir=destination_dir
    )

    assert set(destination_files) == expected_files


def test_should_set_image_original_date(
    year_month_day_dir: Path, destination_dir: Path
) -> None:
    expected_date = datetime.datetime(1993, 3, 21)

    destination_files = vintagexif.vintagexif(
        source_dir=year_month_day_dir, destination_dir=destination_dir
    )

    actual_date = vintagexif.get_media_original_date(destination_files[0])
    assert actual_date == expected_date


def test_should_set_mp4_original_date(mp4_dir: Path, destination_dir: Path) -> None:
    expected_date = datetime.datetime(1997, 9, 28)

    destination_files = vintagexif.vintagexif(
        source_dir=mp4_dir, destination_dir=destination_dir
    )

    actual_date = vintagexif.get_media_original_date(destination_files[0])
    assert actual_date == expected_date


def test_should_preserve_appended_labels(
    appended_label_dir: Path, destination_dir: Path
) -> None:
    expected_file = destination_dir / "1996-08-27_a_label.jpg"

    vintagexif.vintagexif(
        source_dir=appended_label_dir, destination_dir=destination_dir
    )

    actual_file = next(destination_dir.iterdir())
    assert actual_file == expected_file


def test_should_preserve_multiple_labels(
    multiple_appended_labels_dir: Path, destination_dir: Path
) -> None:
    expected_files = {
        destination_dir / "1996-08-27_001_a_label.jpg",
        destination_dir / "1996-08-27_002_another_label.jpg",
    }

    vintagexif.vintagexif(
        source_dir=multiple_appended_labels_dir, destination_dir=destination_dir
    )

    actual_files = set(destination_dir.iterdir())
    assert actual_files == expected_files


def test_should_replace_existing_sequence_and_preserve_label(
    numbered_sources_dir: Path, destination_dir: Path
) -> None:
    expected_files = {
        destination_dir / "1996-08-27_001_trip.jpg",
        destination_dir / "1996-08-27_002.jpg",
    }

    actual_files = vintagexif.vintagexif(
        source_dir=numbered_sources_dir, destination_dir=destination_dir
    )

    assert set(actual_files) == expected_files


def test_should_number_single_digit_video_sequences_per_date(
    short_numbered_videos_dir: Path, destination_dir: Path
) -> None:
    expected_files = {
        destination_dir / "2001-12-05_001.mp4",
        destination_dir / "2001-12-05_002.mp4",
        destination_dir / "2001-12-07.mp4",
    }

    actual_files = vintagexif.vintagexif(
        source_dir=short_numbered_videos_dir, destination_dir=destination_dir
    )

    assert set(actual_files) == expected_files
