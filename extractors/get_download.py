from pathlib import Path
from datetime import datetime

from .config import BASE_DOWNLOAD_DIR


def get_download(website):
    today = datetime.today().strftime("%d-%m-%Y")

    path = BASE_DOWNLOAD_DIR / website / today
    path.mkdir(parents=True, exist_ok=True)

    return path
