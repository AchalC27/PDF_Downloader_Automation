import requests
from datetime import datetime
from bse import BSE

from .get_download import get_download


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.bseindia.com/",
    "Accept": "application/pdf,*/*",
}

SEGMENT = ""


def sanitize(text, max_len=100):
    if not text:
        return "Unknown"

    for ch in r'\/:*?"<>|':
        text = text.replace(ch, "_")

    return text.strip()[:max_len]


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

    # Verify PDF
    with open(path, "rb") as f:
        if f.read(4) != b"%PDF":
            path.unlink(missing_ok=True)
            raise Exception("Downloaded file is not a valid PDF")


def download_bse():

    print("\n========== BSE ==========")

    today = datetime.today().replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0
    )

    download_folder = get_download("bse")

    session = requests.Session()

    downloaded = 0
    skipped = 0

    with BSE(download_folder=str(download_folder)) as bse:

        result = bse.circulars(
            from_date=today,
            to_date=today,
            segment=SEGMENT
        )

        rows = result.get("Table", [])

        print(f"Found {len(rows)} circular(s)")

        for i, row in enumerate(rows, start=1):

            pdf_url = row.get("FileName", "").strip()

            if not pdf_url:
                continue

            notice_no = sanitize(
                row.get("Notice_No") or f"item_{i}"
            )

            subject = sanitize(
                row.get("Subject")
            )

            filename = f"{notice_no}_{subject}.pdf"

            filepath = download_folder / filename

            if filepath.exists():

                skipped += 1

                print(f"Already Exists : {filename}")

                continue

            try:

                download_file(
                    session,
                    pdf_url,
                    filepath
                )

                downloaded += 1

                print(f"Downloaded : {filename}")

            except Exception as e:

                print(f"Failed : {filename}")
                print(e)

    print("\nBSE Summary")
    print("----------------------")
    print(f"Downloaded : {downloaded}")
    print(f"Skipped    : {skipped}")
    print(f"Folder     : {download_folder}")