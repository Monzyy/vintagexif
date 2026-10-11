import datetime
from pathlib import Path
import subprocess
import sys
from typing import List

import pytest

from vintagexif import get_media_original_date

PROJECT_DIR = Path(__file__).resolve().parents[1]
CLI_COMMAND = [sys.executable, "-m", "vintagexif"]
FAILURE_EXIT_CODE = 1
USAGE_ERROR_EXIT_CODE = 2
PROCESS_TIMEOUT_S = 30


def _run_cli(arguments: List[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        CLI_COMMAND + arguments,
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=PROCESS_TIMEOUT_S,
    )


def test_should_describe_source_and_destination_in_cli_help() -> None:
    expected_usage = "SOURCE DESTINATION"

    result = _run_cli(["--help"])

    assert expected_usage in result.stdout


def test_should_require_source_and_destination_arguments() -> None:
    expected_exit_code = USAGE_ERROR_EXIT_CODE

    result = _run_cli([])

    assert result.returncode == expected_exit_code


def test_should_copy_and_date_images_from_the_cli(
    year_month_day_dir: Path, destination_dir: Path
) -> None:
    expected_date = datetime.datetime(1993, 3, 21)
    expected_file = destination_dir / f"{expected_date:%Y-%m-%d}_001.jpg"

    result = _run_cli([str(year_month_day_dir), str(destination_dir)])

    result.check_returncode()
    assert get_media_original_date(expected_file) == expected_date


def test_should_copy_and_date_videos_from_the_cli(
    mp4_dir: Path, destination_dir: Path
) -> None:
    expected_date = datetime.datetime(1997, 9, 28)
    expected_file = destination_dir / f"{expected_date:%Y-%m-%d}_001.mp4"

    result = _run_cli([str(mp4_dir), str(destination_dir)])

    result.check_returncode()
    assert get_media_original_date(expected_file) == expected_date


def test_should_create_nested_destination_directories(
    year_month_day_dir: Path, tmp_path: Path
) -> None:
    destination = tmp_path / "output files" / "dated media"

    result = _run_cli([str(year_month_day_dir), str(destination)])

    result.check_returncode()
    assert destination.is_dir()


def test_should_report_how_many_files_were_processed(
    two_images_same_date_dir: Path, destination_dir: Path
) -> None:
    expected_message = "Processed 2 files"

    result = _run_cli([str(two_images_same_date_dir), str(destination_dir)])

    assert expected_message in result.stdout


def test_should_report_missing_source_without_a_traceback(tmp_path: Path) -> None:
    source = tmp_path / "missing"
    destination = tmp_path / "output"
    expected_error = "vintagexif: error: source_dir is not a directory\n"

    result = _run_cli([str(source), str(destination)])

    assert result.stderr == expected_error


def test_should_exit_unsuccessfully_for_invalid_source(tmp_path: Path) -> None:
    source = tmp_path / "missing"
    destination = tmp_path / "output"

    result = _run_cli([str(source), str(destination)])

    assert result.returncode == FAILURE_EXIT_CODE


@pytest.mark.parametrize("destination_name", [".", "output"])
def test_should_reject_destination_inside_source(
    tmp_path: Path, destination_name: str
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    destination = source / destination_name
    expected_error = "destination must be outside the source directory"

    result = _run_cli([str(source), str(destination)])

    assert expected_error in result.stderr


def test_should_reject_nonempty_destination_without_overwriting_files(
    year_month_day_dir: Path, destination_dir: Path
) -> None:
    destination_dir.mkdir()
    existing_file = destination_dir / "1993-03-21_001.jpg"
    original_bytes = b"existing output"
    existing_file.write_bytes(original_bytes)

    _run_cli([str(year_month_day_dir), str(destination_dir)])

    assert existing_file.read_bytes() == original_bytes


def test_should_report_when_no_dated_files_are_found(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    destination = tmp_path / "destination"
    expected_message = "No dated media files found"

    result = _run_cli([str(source), str(destination)])

    assert expected_message in result.stdout


def test_should_report_missing_exiftool(
    mp4_dir: Path, destination_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PATH", "")
    expected_error = '"exiftool" is not found'

    result = _run_cli([str(mp4_dir), str(destination_dir)])

    assert expected_error in result.stderr.lower()


def test_should_report_invalid_media_without_a_traceback(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "1997-09-28.mp4").write_bytes(b"not a video")
    destination = tmp_path / "destination"
    expected_prefix = "vintagexif: error:"

    result = _run_cli([str(source), str(destination)])

    assert result.stderr.startswith(expected_prefix)
