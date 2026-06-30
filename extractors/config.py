from pathlib import Path

from pathlib import Path

# Folder one level above config.py
PROJECT_DIR = Path(__file__).resolve().parent.parent

# Create downloads folder there
BASE_DOWNLOAD_DIR = PROJECT_DIR / "downloads"
BASE_DOWNLOAD_DIR.mkdir(exist_ok=True)
LOG_DIR = PROJECT_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

SEEN_DIR = PROJECT_DIR / "seen"
SEEN_DIR.mkdir(exist_ok=True)

SCHEDULE_TIME = "09:43"
REQUEST_TIMEOUT = 60

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}