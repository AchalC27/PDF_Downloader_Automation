import requests
from datetime import datetime

from bse import BSE

from .logger import get_logger
from .get_download import get_download
from .json_handler import (
    get_json_file,
    load_downloaded_urls,
    save_downloaded_urls,
)

logger = get_logger("bse")


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.bseindia.com/",
    "Accept": "application/pdf,*/*",
}

SEGMENT = ""


def sanitize(text, max_len=100):

    if not text:
        return "Unknown"

    for ch in r'\\/:*?"<>|':
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

    with open(path, "wb") as file:

        for chunk in response.iter_content(16384):

            if chunk:

                file.write(chunk)

    with open(path, "rb") as file:

        if file.read(4) != b"%PDF":

            path.unlink(missing_ok=True)

            raise Exception("Downloaded file is not a valid PDF")


def download_bse():

    logger.info("")
    logger.info("========== BSE ==========")

    today = datetime.today().replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0
    )

    download_folder = get_download("bse")

    json_file = get_json_file("bse")

    processed_urls = load_downloaded_urls(
        json_file
    )

    session = requests.Session()

    downloaded = 0
    failed = 0

    with BSE(download_folder=str(download_folder)) as bse:

        result = bse.circulars(
            from_date=today,
            to_date=today,
            segment=SEGMENT
        )

        rows = result.get("Table", [])

        total = len(rows)

        logger.info(
            f"Total Circulars Found : {total}"
        )

        new_rows = []

        for row in rows:

            pdf_url = row.get(
                "FileName",
                ""
            ).strip()

            if not pdf_url:
                continue

            if pdf_url not in processed_urls:

                new_rows.append(row)

        already_processed = total - len(new_rows)

        logger.info(
            f"Already Processed     : {already_processed}"
        )

        if not new_rows:

            logger.info(
                "No new circulars found."
            )

            return

        try:

            for i, row in enumerate(
                new_rows,
                start=1
            ):

                pdf_url = row["FileName"].strip()

                notice_no = sanitize(
                    row.get("Notice_No")
                    or f"item_{i}"
                )

                subject = sanitize(
                    row.get("Subject")
                )

                filename = (
                    f"{notice_no}_{subject}.pdf"
                )

                filepath = (
                    download_folder / filename
                )

                try:

                    logger.info(
                        f"Downloading : {filename}"
                    )

                    download_file(
                        session,
                        pdf_url,
                        filepath
                    )

                    downloaded += 1

                except Exception:

                    failed += 1

                    logger.exception(
                        f"Failed : {filename}"
                    )

                finally:

                    processed_urls.add(
                        pdf_url
                    )

        finally:

            save_downloaded_urls(
                json_file,
                processed_urls
            )

    logger.info("")
    logger.info("BSE Summary")
    logger.info("--------------------------")
    logger.info(
        f"Total Circulars Found : {total}"
    )
    logger.info(
        f"Already Processed     : {already_processed}"
    )
    logger.info(
        f"Downloaded            : {downloaded}"
    )
    logger.info(
        f"Failed                : {failed}"
    )

