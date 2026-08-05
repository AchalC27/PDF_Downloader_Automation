import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from .logger import get_logger
from .helpers import load_seen, save_seen, dest_for, download_pdf
from .db import pdf_exists, save_pdf

logger = get_logger("cdsl")

BASE_URL = "https://www.cdslindia.com"
PAGE_URL = f"{BASE_URL}/eservices/Publications/Communique"
DOWNLOAD_URL = f"{BASE_URL}/eservices/Publications/DownloadFile"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    ),
    "X-Requested-With": "XMLHttpRequest",
    "Referer": PAGE_URL,
}

DATE_FORMAT = "%d-%b-%Y"


def fetch_communiques(session):
    response = session.get(PAGE_URL, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    table = soup.find("tbody", id="tblCommuniquDtlBody")

    if table is None:
        logger.error("Communique table not found.")
        return []

    items = []

    for row in table.find_all("tr"):

        cols = row.find_all("td")

        if len(cols) < 4:
            continue

        comm_id = cols[0].get_text(strip=True)

        link = cols[1].find("a")

        subject = link.get_text(" ", strip=True)

        date = cols[3].get_text(strip=True)

        department = cols[2].get_text(strip=True)

        items.append(
            {
                "id": comm_id,
                "date": date,
                "subject": subject,
                "attachment": f"{DOWNLOAD_URL}?eventID={comm_id}&method=communique",
                "label": department or "General",
            }
        )

    return items


def sanitize_filename(name):
    return re.sub(r'[<>:"/\\|?*]', "_", name)


def expected_filename(item):
    subject = sanitize_filename(item["subject"] or "communique")[:150]
    return f'{item["id"]}_{subject}.pdf'


def download_cdsl():
    logger.info("")
    logger.info("========== CDSL ==========")

    session = requests.Session()
    session.headers.update(HEADERS)

    seen = load_seen("cdsl")

    items = fetch_communiques(session)

    # import timedelta
    # yesterday = (datetime.now() - timedelta(days=1)).strftime(DATE_FORMAT)

    #today = datetime(2026, 7, 31, 12, 0, 0).strftime(DATE_FORMAT)

    today = datetime.now().strftime(DATE_FORMAT)
    items = [
        item
        for item in items
        if item["date"] == today
    ]

    total = len(items)

    logger.info(f"Total Communiques Found : {total}")

    downloaded = 0
    failed = 0
    already_processed = 0

    for item in items:

        filename = expected_filename(item)

        if pdf_exists("CDSL", filename) or item["attachment"] in seen:
            already_processed += 1
            continue

        try:

            dest = dest_for("CDSL", filename)

            if not download_pdf(item["attachment"], dest, logger, session=session):
                failed += 1
                continue

            save_pdf(
                source="CDSL",
                pdf_name=filename,
                pdf_link=item["attachment"],
                category=item["label"],
            )

            seen.add(item["attachment"])

            logger.info(f"Saved : {filename}")

            downloaded += 1

        except Exception:

            failed += 1
            logger.exception(f"Failed : {item['id']}")

    save_seen("cdsl", seen)

    logger.info("")
    logger.info("CDSL Summary")
    logger.info("-------------------------")
    logger.info(f"Total Communiques Found : {total}")
    logger.info(f"Already Processed       : {already_processed}")
    logger.info(f"Downloaded              : {downloaded}")
    logger.info(f"Failed                  : {failed}")