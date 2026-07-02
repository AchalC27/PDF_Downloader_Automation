import requests
from datetime import datetime
import re

from bse import BSE

from .logger import get_logger
from .get_download import get_download
from .db import pdf_exists, save_pdf

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

    # Remove newlines/tabs
    text = re.sub(r"[\r\n\t]+", " ", text)

    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text)

    # Replace invalid filename characters
    text = re.sub(r'[\\/:*?"<>|]', "_", text)

    return text.strip()[:max_len]


def download_file(session, url, path):
    response = session.get(url, headers=HEADERS, stream=True, timeout=60)
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

    today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)

    download_folder = get_download("bse")

    session = requests.Session()

    downloaded = 0
    failed = 0
    already_processed = 0

    with BSE(download_folder=str(download_folder)) as bse:
        result = bse.circulars(from_date=today, to_date=today, segment=SEGMENT)
        rows = result.get("Table", [])
        total = len(rows)

        logger.info(f"Total Circulars Found : {total}")

        new_rows = []

        for i, row in enumerate(rows, start=1):
            pdf_url = row.get("FileName", "").strip()

            if not pdf_url:
                continue

            notice_no = sanitize(row.get("Notice_No") or f"item_{i}")
            subject = sanitize(row.get("Subject"))
            filename = f"{notice_no}_{subject}.pdf"

            if pdf_exists("BSE", filename):
                already_processed += 1
                continue

            new_rows.append((row, filename))

        logger.info(f"Already Processed     : {already_processed}")

        if not new_rows:
            logger.info("No new circulars found.")
            return

        for row, filename in new_rows:
            pdf_url = row["FileName"].strip()
            category = row.get("Category") or "Uncategorized"
            filepath = download_folder / filename

            try:
                logger.info(f"Downloading : {filename}")

                download_file(session, pdf_url, filepath)

                save_pdf(
                    source="BSE",
                    pdf_name=filename,
                    pdf_link=pdf_url,
                    category=category,
                )

                downloaded += 1

            except Exception:
                failed += 1
                logger.exception(f"Failed : {filename}")

    logger.info("")
    logger.info("BSE Summary")
    logger.info("--------------------------")
    logger.info(f"Total Circulars Found : {total}")
    logger.info(f"Already Processed     : {already_processed}")
    logger.info(f"Downloaded            : {downloaded}")
    logger.info(f"Failed                : {failed}")