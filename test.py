import hashlib
import os
import requests

from .db import pdf_exists, save_pdf
from .logger import get_logger

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
    "Referer": "https://www.arclindia.com/media/circulars"
}


def fetch_documents():
    page = 1
    limit = 20

    documents = []

    while True:

        response = requests.get(
            API_URL,
            headers=HEADERS,
            params={
                "page": page,
                "limit": limit
            },
            timeout=30,
            verify=False          # Remove when ARCL fixes SSL
        )

        response.raise_for_status()

        data = response.json()

        # change this if your response uses another key
        records = data.get("data", [])

        if not records:
            break

        documents.extend(records)

        if len(records) < limit:
            break

        page += 1

    return documents


def generate_filename(document_url):

    original = document_url.split("/")[-1]

    base, ext = os.path.splitext(original)

    hashcode = hashlib.md5(
        document_url.encode("utf-8")
    ).hexdigest()[:8]

    return f"{base}_{hashcode}{ext}"


def save_documents(records):

    saved = 0
    failed = 0

    for item in records:

        try:

            pdf_url = item.get("pdf_url")

            if not pdf_url:
                continue

            if pdf_url.startswith("/"):
                pdf_url = BASE_URL + pdf_url

            filename = generate_filename(pdf_url)

            logger.info(f"Saving : {filename}")

            save_pdf(
                source="ARCL",
                pdf_name=filename,
                pdf_link=pdf_url,
                category="Circulars"
            )

            saved += 1

        except Exception:
            logger.exception("Failed saving record")
            failed += 1

    return saved, failed


def download_arcl():

    logger.info("")
    logger.info("========== ARCL ==========")

    records = fetch_documents()

    logger.info(f"Total Documents Found : {len(records)}")

    new_records = []

    for item in records:

        pdf_url = item.get("pdf_url")

        if not pdf_url:
            continue

        if pdf_url.startswith("/"):
            pdf_url = BASE_URL + pdf_url

        filename = generate_filename(pdf_url)

        if pdf_exists("ARCL", filename):
            continue

        item["pdf_url"] = pdf_url

        new_records.append(item)

    already_processed = len(records) - len(new_records)

    logger.info(f"Already Processed : {already_processed}")

    if not new_records:

        logger.info("No new documents found.")
        return

    saved, failed = save_documents(new_records)

    logger.info("")
    logger.info("ARCL Summary")
    logger.info("-------------------------")
    logger.info(f"Total Documents Found : {len(records)}")
    logger.info(f"Already Processed     : {already_processed}")
    logger.info(f"Saved To Database     : {saved}")
    logger.info(f"Failed                : {failed}")