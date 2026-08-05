import re
import time
from datetime import date, datetime

import requests

from .logger import get_logger
from .helpers import load_seen, save_seen, dest_for, download_pdf
from .db import pdf_exists, save_pdf

logger = get_logger("mcx")

DELAY = 0.5

API_URL = "https://www.mcxindia.com/circulars/all-circulars/GetFilteredAnnouncements"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.mcxindia.com/circulars/all-circulars",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
}

DATE_FORMATS = ["%d-%m-%Y"]


def parse_date(text):
    text = text.strip()

    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).strftime("%d/%m/%Y")
        except ValueError:
            pass

    raise ValueError(f"Invalid date : {text}")


def fetch_all_pages(from_date, to_date, category="", title="", circular_no=""):
    session = requests.Session()
    session.headers.update(HEADERS)

    seen = set()
    circulars = []
    page = 1

    while True:
        params = {
            "CircularTitle": title,
            "CircularsCategory": category,
            "CircularNo": circular_no,
            "fromdate": from_date,
            "todate": to_date,
            "page": page,
        }

        logger.info(f"Fetching page {page}")

        response = session.get(API_URL, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()

        if not data.get("success"):
            break

        total_pages = data.get("TotalPages", 1)
        total_items = data.get("TotalItems", 0)

        if page == 1 and data.get("AllResult"):
            items = data["AllResult"]
            use_all = True
        else:
            items = data.get("Announcements") or []
            use_all = False

        for item in items:
            number = item.get("CircularNo", "")

            if number not in seen:
                seen.add(number)
                circulars.append(item)

        logger.info(f"Page {page}/{total_pages}")

        if (use_all and len(circulars) >= total_items) or page >= total_pages:
            break

        page += 1

    return circulars


def clean_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "_", name).strip()


def build_filename(item):
    return (
        f"{clean_filename(item.get('Title', 'untitled'))}"
    )


def download_pdfs(circulars, seen):
    downloaded = 0
    failed = 0

    for item, filename in circulars:

        pdf_url = item.get("CircularFile", "").strip()

        if not pdf_url:
            continue

        category = item.get("CircularsCategory") or "Uncategorized"

        logger.info(f"Saving : {filename}")

        dest = dest_for("MCX", filename)

        if not download_pdf(pdf_url, dest, logger, extra_headers=HEADERS):
            failed += 1
            time.sleep(DELAY)
            continue

        try:
            save_pdf(
                source="MCX",
                pdf_name=filename,
                pdf_link=pdf_url,
                category=category,
            )

            seen.add(pdf_url)
            downloaded += 1

        except Exception:
            failed += 1
            logger.exception(f"Failed : {filename}")

        time.sleep(DELAY)

    return downloaded, failed


def download_mcx():
    logger.info("")
    logger.info("========== MCX ==========")

    today = date.today().strftime("%d/%m/%Y")

    seen = load_seen("mcx")

    circulars = fetch_all_pages(from_date=today, to_date=today)

    total = len(circulars)

    logger.info(f"Total Circulars Found : {total}")

    new_circulars = []
    already_processed = 0

    for item in circulars:
        pdf_url = item.get("CircularFile", "").strip()

        if not pdf_url:
            continue

        filename = build_filename(item)

        if pdf_exists("MCX", filename) or pdf_url in seen:
            already_processed += 1
            continue

        new_circulars.append((item, filename))

    logger.info(f"Already Processed     : {already_processed}")

    if not new_circulars:
        logger.info("No new circulars found.")
        save_seen("mcx", seen)
        return

    downloaded, failed = download_pdfs(new_circulars, seen)

    save_seen("mcx", seen)

    logger.info("")
    logger.info("MCX Summary")
    logger.info("-------------------------")
    logger.info(f"Total Circulars Found : {total}")
    logger.info(f"Already Processed     : {already_processed}")
    logger.info(f"Downloaded            : {downloaded}")
    logger.info(f"Failed                : {failed}")