import json
from pathlib import Path


JSON_FOLDER = Path("json")

JSON_FOLDER.mkdir(
    parents=True,
    exist_ok=True
)


def get_json_file(website):

    return JSON_FOLDER / f"{website.lower()}.json"


def load_downloaded_urls(json_file):

    if json_file.exists():

        try:

            with open(json_file, "r", encoding="utf-8") as f:

                return set(json.load(f))

        except Exception:

            return set()

    return set()


def save_downloaded_urls(
    json_file,
    downloaded_urls
):

    with open(json_file, "w", encoding="utf-8") as f:

        json.dump(
            sorted(downloaded_urls),
            f,
            indent=4
        )