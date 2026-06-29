import requests
from datetime import datetime
from nse import NSE
from .get_download import get_download
NSE_ARCHIVE_URL = "https://nsearchives.nseindia.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.nseindia.com/",
    "Accept": "*/*",
}
def sanitize(text, max_len=100):
    if not text:
        return "Unknown"

    for ch in r'\/:*?"<>|':
        text = text.replace(ch, "_")

    return text.strip()[:max_len]


def build_url(row):

    link = row.get("circFilelink", "").strip()

    if not link:
        return None

    if link.startswith("http"):
        return link

    if link.startswith("/"):
        return NSE_ARCHIVE_URL + link

    return NSE_ARCHIVE_URL + "/" + link


def download_file(session, url, path):

    response = session.get(
        url,
        headers=HEADERS,
        stream=True,
        timeout=60
    )

    response.raise_for_status()

    with open(path, "wb") as f:
        for chunk in response.iter_content(16384):
            if chunk:
                f.write(chunk)


def download_nse():

    print("\n========== NSE ==========")

    today = datetime.today().replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0
    )

    download_folder = get_download("nse")

    session = requests.Session()

    downloaded = 0
    skipped = 0
    with NSE(download_folder=str(download_folder)) as nse:

        result = nse.circulars(
            from_date=today,
            to_date=today
        )

        if isinstance(result, dict):
            rows = result.get("data", result.get("Table", []))
        else:
            rows = result

        target = today.strftime("%Y%m%d")

        rows = [
            row
            for row in rows
            if str(row.get("cirDate")) == target
        ]

        print(f"Found {len(rows)} circular(s)")

        for i, row in enumerate(rows, start=1):

            url = build_url(row)

            if not url:
                continue

            number = sanitize(
                row.get("circDisplayNo")
                or row.get("circNumber")
                or f"item_{i}"
            )

            subject = sanitize(
                row.get("sub")
            )

            ext = (
                row.get("fileExt")
                or "pdf"
            ).lower()

            filename = f"{number}_{subject}.{ext}"

            filepath = download_folder / filename

            if filepath.exists():
                skipped += 1
                print(f"Already Exists : {filename}")
                continue

            try:

                download_file(
                    session,
                    url,
                    filepath
                )

                downloaded += 1
                print(f"Downloaded : {filename}")

            except Exception as e:

                print(f"Failed : {filename}")
                print(e)

    print("\nNSE Summary")
    print("---------------------")
    print(f"Downloaded : {downloaded}")
    print(f"Skipped    : {skipped}")
    print(f"Folder     : {download_folder}")