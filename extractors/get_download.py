from pathlib import Path
from datetime import datetime


def get_download(website):
    today = datetime.today().strftime("%d-%m-%Y")

    # Only return the path.
    # Do NOT create any directories.
    return Path("downloads") / website / today