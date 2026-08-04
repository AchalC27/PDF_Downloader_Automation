import re
from datetime import datetime

from nse import NSE

from .logger import get_logger
from .get_download import get_download
from .helpers import load_seen, save_seen
from .db import pdf_exists, save_pdf

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
    seen = load_seen("nse")

    downloaded = 0
    failed = 0
    already_processed = 0

    with NSE(download_folder=str(download_folder)) as nse:

        result = nse.circulars(
            from_date=today,
            to_date=today,
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

        total = len(rows)

        logger.info(f"Total Circulars Found : {total}")

        new_rows = []

        for i, row in enumerate(rows, start=1):

            url = build_url(row)

            if not url:
                continue

            number = sanitize(
                row.get("circDisplayNo")
                or row.get("circNumber")
                or f"item_{i}"
            )

            subject = sanitize(row.get("sub"))

            ext = (row.get("fileExt") or "pdf").lower()

            filename = f"{number}_{subject}.{ext}"

            if pdf_exists("NSE", filename) or url in seen:
                already_processed += 1
                continue

            new_rows.append((row, url, filename))

        logger.info(f"Already Processed     : {already_processed}")

        if not new_rows:
            logger.info("No new circulars found.")
            save_seen("nse", seen)
            return

        for row, url, filename in new_rows:

            category = row.get("Category") or "Uncategorized"

            try:
                logger.info(f"Downloading : {filename}")

                saved_path = nse.download_document(url, folder=download_folder)

                target_path = download_folder / filename

                if saved_path != target_path:
                    saved_path.replace(target_path)

                save_pdf(
                    source="NSE",
                    pdf_name=filename,
                    pdf_link=url,
                    category=category,
                )

                seen.add(url)
                downloaded += 1

            except Exception:
                failed += 1
                logger.exception(f"Failed : {filename}")

    save_seen("nse", seen)

    logger.info("")
    logger.info("NSE Summary")
    logger.info("-------------------------")
    logger.info(f"Total Circulars Found : {total}")
    logger.info(f"Already Processed     : {already_processed}")
    logger.info(f"Downloaded            : {downloaded}")
    logger.info(f"Failed                : {failed}")