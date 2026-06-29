from pathlib import Path
from datetime import datetime
def get_download(website):
    today = datetime.today().strftime("%d-%m-%Y")
    folder = Path("downloads") / website / today
    folder.mkdir(
        parents=True,
        exist_ok=True
    )

    return folder