from pathlib import Path


def setup_folders(source_folder):
    source = Path(source_folder)
    archive_dir = source / "Archive"
    failed_dir = source / "Failed"
    archive_dir.mkdir(exist_ok=True)
    failed_dir.mkdir(exist_ok=True)
    return archive_dir , failed_dir , source
