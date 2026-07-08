import re
from datetime import datetime

import requests
from nse import NSE

from .logger import get_logger
from .get_download import get_download
from .db import pdf_exists, save_pdf

logger = get_logger("nse")

NSE_ARCHIVE_URL = "https://nsearchives.nseindia.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.nseindia.com/",
}


def sanitize(text, max_len=120):
    if not text:
        return "Unknown"

    text = re.sub(r"[\r\n\t]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r'[\\/:*?"<>|]', "_", text)

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

    downloaded = 0
    already_processed = 0
    failed = 0

    target_date = today.strftime("%Y%m%d")

    # Prevent duplicate rows returned by NSE API
    processed_files = set()

    with NSE(download_folder=str(download_folder)) as nse:

        result = nse.circulars(
            from_date=today,
            to_date=today,
        )

        if isinstance(result, dict):
            rows = result.get("data", result.get("Table", []))
        else:
            rows = result

        rows = [
            row
            for row in rows
            if str(row.get("cirDate")) == target_date
        ]

        logger.info(f"Total Circulars Found : {len(rows)}")

        for index, row in enumerate(rows, start=1):

            try:

                url = build_url(row)

                if not url:
                    continue

                number = sanitize(
                    row.get("circDisplayNo")
                    or row.get("circNumber")
                    or f"item_{index}"
                )

                subject = sanitize(row.get("sub"))

                ext = (row.get("fileExt") or "pdf").lower()

                filename = f"{number}_{subject}.{ext}"

                category = row.get("Category") or "Uncategorized"

                # Skip duplicate entries returned by NSE API
                if filename in processed_files:
                    logger.info(f"Duplicate API entry skipped : {filename}")
                    continue

                processed_files.add(filename)

                # Already present in database?
                if pdf_exists("NSE", filename):
                    already_processed += 1
                    continue

                logger.info(f"Saving : {filename}")

                save_pdf(
                    source="NSE",
                    pdf_name=filename,
                    pdf_link=url,
                    category=category,
                )

                downloaded += 1

            except Exception:
                failed += 1
                logger.exception(f"Failed : {filename}")

    logger.info("")
    logger.info("NSE Summary")
    logger.info("----------------------------")
    logger.info(f"Total Circulars Found : {len(rows)}")
    logger.info(f"Already Processed     : {already_processed}")
    logger.info(f"Downloaded            : {downloaded}")
    logger.info(f"Failed                : {failed}")