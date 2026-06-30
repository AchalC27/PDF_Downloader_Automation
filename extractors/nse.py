import requests
from datetime import datetime

from nse import NSE

from .logger import get_logger
from .get_download import get_download
from .json_handler import (
    get_json_file,
    load_downloaded_urls,
    save_downloaded_urls,
)

logger = get_logger("nse")

NSE_ARCHIVE_URL = "https://nsearchives.nseindia.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.nseindia.com/",
    "Accept": "*/*",
}


def sanitize(text, max_len=100):

    if not text:
        return "Unknown"

    for ch in r'\\/:*?"<>|':
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
        timeout=60,
    )

    response.raise_for_status()

    with open(path, "wb") as file:

        for chunk in response.iter_content(16384):

            if chunk:

                file.write(chunk)


def download_nse():

    logger.info("")
    logger.info("========== NSE ==========")

    today = datetime.today().replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    download_folder = get_download("nse")

    json_file = get_json_file("nse")

    processed_urls = load_downloaded_urls(
        json_file
    )

    session = requests.Session()

    downloaded = 0
    failed = 0

    with NSE(download_folder=str(download_folder)) as nse:

        result = nse.circulars(
            from_date=today,
            to_date=today,
        )

        if isinstance(result, dict):

            rows = result.get(
                "data",
                result.get("Table", []),
            )

        else:

            rows = result

        target = today.strftime("%Y%m%d")

        rows = [

            row

            for row in rows

            if str(row.get("cirDate")) == target

        ]

        total = len(rows)

        logger.info(
            f"Total Circulars Found : {total}"
        )

        new_rows = []

        for row in rows:

            url = build_url(row)

            if not url:
                continue

            if url not in processed_urls:

                new_rows.append(row)

        already_processed = (
            total - len(new_rows)
        )

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
                start=1,
            ):

                url = build_url(row)

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

                filename = (
                    f"{number}_{subject}.{ext}"
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
                        url,
                        filepath,
                    )

                    downloaded += 1

                except Exception:

                    failed += 1

                    logger.exception(
                        f"Failed : {filename}"
                    )

                finally:

                    processed_urls.add(url)

        finally:

            save_downloaded_urls(
                json_file,
                processed_urls,
            )

    logger.info("")
    logger.info("NSE Summary")
    logger.info("-------------------------")
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

