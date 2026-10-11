# Vintagexif

Copy photos and videos into a destination folder, using dates inferred from
filenames or year/month/day folders to set their recording dates.

## Installation

Use Python 3.9 or newer. From this repository, install the command:

```sh
python -m pip install .
```

For videos, also install the [ExifTool executable](https://exiftool.org/) on your
PATH. PyExifTool is a Python wrapper and does not include that executable.

## Command line

```sh
vintagexif "path/to/source media" "path/to/dated output"
vintagexif --help
```

You can also run it directly from the repository:

```sh
python -m vintagexif "path/to/source media" "path/to/dated output"
```

The source is searched recursively. The destination must be new or empty and
outside the source directory; missing parent directories are created. Originals
remain in the source folder. The CLI refuses nonempty destinations to avoid
overwriting a previous run.

Dates come from a `YYYY-MM-DD` or `YYYY_MM_DD` filename prefix, or numeric
`year/month/day` directories. A year alone defaults to January 1, and a year/month
defaults to the first day. Directory dates take precedence over filename dates.
Files with no inferred date are skipped. Output files are named like
`1997-09-28_001.mp4`, retaining labels appended to `YYYY-MM-DD` filenames.

The command prints how many files it processed, or reports that no dated files
were found. Exit codes are `0` for success, `1` for processing errors, `2` for
invalid command-line arguments, and `130` for interruption. On failure, files
already processed remain in the destination; use a new output directory to retry.

## Python API

```python
from pathlib import Path
from vintagexif import vintagexif

vintagexif(Path("source"), Path("destination"))
```

## MP4 dates and Nextcloud Memories

Memories prefers `ContentCreateDate`, then `CreationDate`, then `CreateDate`
for videos ([date-selection implementation](https://github.com/pulsejet/memories/blob/master/lib/Exif.php)).
Changing only filesystem dates or the MP4 movie header can leave an older,
higher-priority recording date in place.

Vintagexif updates those embedded QuickTime dates along with movie, track,
and media header timestamps. Dates without timezone information (including
filename/folder dates) are treated as UTC. Timezone-aware dates passed to
`set_media_original_date` retain their offset in text metadata, while binary
QuickTime timestamps are stored in UTC. `get_media_original_date` returns
the embedded wall-clock date without timezone information, as it does for images.
If a video has no recording date, or its highest-priority date field is invalid,
the getter raises `ValueError` rather than silently selecting a different date.

Regenerate the output files and upload them to Nextcloud. If you replace files
that Memories has already indexed, force a metadata refresh on the server:

```sh
php occ memories:index --force
```

Run this from your Nextcloud installation using its normal service account or
container command. The command refreshes all existing index entries; see the
[Memories documentation](https://memories.gallery/occ-commands/) for `--user`
and `--path` filters. If files were changed directly in Nextcloud's storage,
refresh Nextcloud's file cache with its `files:scan` command first.

## Tests

The media fixtures use Git LFS. Download them before running the tests:

```sh
git lfs pull
python -m pip install -r requirements.txt
python -m pytest
```
