import re
import tempfile
from datetime import datetime

from bse import BSE

from .logger import get_logger
from .db import pdf_exists, save_pdf

logger = get_logger("bse")

SEGMENT = ""


def sanitize(text, max_len=100):
    if not text:
        return "Unknown"

    text = re.sub(r"[\r\n\t]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r'[\\/:*?"<>|]', "_", text)

    return text.strip()[:max_len]


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

    # Temporary folder required only because the BSE package expects one.
    # No PDFs will be downloaded or stored.
    with tempfile.TemporaryDirectory() as temp_dir:

        with BSE(download_folder=temp_dir) as bse:

            result = bse.circulars(
                from_date=today,
                to_date=today,
                segment=SEGMENT,
            )

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

                try:
                    logger.info(f"Saving : {filename}")

                    save_pdf(
                        source="BSE",
                        pdf_name=filename,
                        pdf_link=row["FileName"].strip(),
                        category=row.get("Category") or "Uncategorized",
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