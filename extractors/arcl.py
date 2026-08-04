import hashlib
import os
from datetime import datetime, timezone

import requests
import urllib3

from .db import pdf_exists, save_pdf
from .logger import get_logger
from .helpers import load_seen, save_seen, dest_for, download_pdf

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = get_logger("arcl")

API_URL = "https://www.arclindia.com/api/circulars/public"
BASE_URL = "https://www.arclindia.com"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/137.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}


def generate_filename(document_url):
    original = document_url.split("/")[-1]

    base, ext = os.path.splitext(original)

    url_hash = hashlib.md5(
        document_url.encode("utf-8")
    ).hexdigest()[:8]

    return f"{base}_{url_hash}{ext}"


def fetch_today_records():

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    page = 1
    limit = 20

    today_records = []

    while True:

        response = requests.get(
            API_URL,
            headers=HEADERS,
            params={
                "page": page,
                "limit": limit
            },
            timeout=30,
            verify=False
        )

        response.raise_for_status()

        payload = response.json()

        records = payload.get("data", [])

        if not records:
            break

        stop_fetching = False

        for record in records:

            created_date = record["created_at"][:10]

            if created_date != today:
                stop_fetching = True
                break

            today_records.append(record)

        if stop_fetching:
            break

        if len(records) < limit:
            break

        page += 1

    return today_records


def save_documents(records, seen):

    saved = 0
    skipped = 0
    failed = 0

    for record in records:

        try:

            pdf_url = record.get("pdf_url")

            if not pdf_url:
                continue

            if pdf_url.startswith("/"):
                pdf_url = BASE_URL + pdf_url

            filename = generate_filename(pdf_url)

            if pdf_exists("ARCL", filename) or pdf_url in seen:
                logger.info(f"Already Processed : {filename}")
                skipped += 1
                continue

            logger.info(f"Saving : {filename}")

            dest = dest_for("ARCL", filename)

            if not download_pdf(pdf_url, dest, logger):
                failed += 1
                continue

            save_pdf(
                source="ARCL",
                pdf_name=filename,
                pdf_link=pdf_url,
                category="Circulars"
            )

            seen.add(pdf_url)
            saved += 1

        except Exception:
            logger.exception("Failed Saving Document")
            failed += 1

    return saved, skipped, failed


def download_arcl():

    logger.info("")
    logger.info("========== ARCL ==========")

    seen = load_seen("arcl")

    today_records = fetch_today_records()

    logger.info(f"Today's Circulars Found : {len(today_records)}")

    if not today_records:
        logger.info("No circulars published today.")
        save_seen("arcl", seen)
        return

    saved, skipped, failed = save_documents(today_records, seen)

    save_seen("arcl", seen)

    logger.info("")
    logger.info("ARCL Summary")
    logger.info("------------------------------------")
    logger.info(f"Today's Circulars : {len(today_records)}")
    logger.info(f"Saved             : {saved}")
    logger.info(f"Already Processed : {skipped}")
    logger.info(f"Failed            : {failed}")