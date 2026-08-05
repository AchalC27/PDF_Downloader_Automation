import re
import time
from datetime import datetime
from urllib.parse import urljoin

import requests
from bse import BSE

from .logger import get_logger
from .get_download import get_download
from .helpers import load_seen, save_seen
from .db import pdf_exists, save_pdf

logger = get_logger("bse")

SEGMENT = ""

MAX_RETRIES = 3
RETRY_DELAY = 5 


def sanitize(text, max_len=100):
    if not text:
        return "Unknown"

    text = re.sub(r"[\r\n\t]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r'[\\/:*?"<>|]', "_", text)

    return text.strip()[:max_len]


def fetch_circulars(bse, from_date, to_date, segment):

    delay = RETRY_DELAY

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return bse.circulars(
                from_date=from_date,
                to_date=to_date,
                segment=segment,
            )
        except (TimeoutError, requests.exceptions.RequestException) as exc:
            logger.warning(
                f"BSE circulars request failed (attempt {attempt}/{MAX_RETRIES}): {exc}"
            )

            if attempt == MAX_RETRIES:
                raise

            time.sleep(delay)
            delay *= 2


def download_bse():
    logger.info("")
    logger.info("========== BSE ==========")

    today = datetime.today().replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    downloaded = 0
    failed = 0
    already_processed = 0
    download_folder = get_download("bse")
    seen = load_seen("bse")

    with BSE(download_folder=str(download_folder)) as bse:

        try:
            result = fetch_circulars(bse, today, today, SEGMENT)
        except (TimeoutError, requests.exceptions.RequestException):
            logger.error(
                "BSE circulars endpoint did not respond after "
                f"{MAX_RETRIES} attempts. Skipping this run."
            )
            save_seen("bse", seen)
            return

        rows = result.get("Table", [])
        total = len(rows)

        logger.info(f"Total Circulars Found : {total}")

        new_rows = []

        for i, row in enumerate(rows, start=1):

            pdf_url = row.get("FileName", "").strip()

            if not pdf_url:
                continue

            notice_no = sanitize(
                row.get("Notice_No") or f"item_{i}"
            )

            subject = sanitize(row.get("Subject"))

            filename = f"{subject}"

            if pdf_exists("BSE", filename) or pdf_url in seen:
                already_processed += 1
                continue

            new_rows.append((row, filename))

        logger.info(f"Already Processed     : {already_processed}")

        if not new_rows:
            logger.info("No new circulars found.")
            save_seen("bse", seen)
            return

        for row, filename in new_rows:

            pdf_url = row["FileName"].strip()
            full_url = urljoin(BSE.base_url, pdf_url)

            try:
                logger.info(f"Downloading : {filename}")

                dest = download_folder / filename

                with bse.session.get(full_url, stream=True, timeout=60) as resp:
                    if resp.status_code == 404:
                        logger.warning(f"Broken document link (404): {full_url}")
                        failed += 1
                        continue

                    resp.raise_for_status()

                    with open(dest, "wb") as f:
                        for chunk in resp.iter_content(chunk_size=8192):
                            f.write(chunk)

                save_pdf(
                    source="BSE",
                    pdf_name=filename,
                    pdf_link=full_url,
                    category=row.get("Category") or "Uncategorized",
                )

                seen.add(pdf_url)
                downloaded += 1

            except Exception:
                failed += 1
                logger.exception(f"Failed : {filename}")

    save_seen("bse", seen)

    logger.info("")
    logger.info("BSE Summary")
    logger.info("--------------------------")
    logger.info(f"Total Circulars Found : {total}")
    logger.info(f"Already Processed     : {already_processed}")
    logger.info(f"Downloaded            : {downloaded}")
    logger.info(f"Failed                : {failed}")