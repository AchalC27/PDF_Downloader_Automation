import hashlib
import os
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from extractors.json_handler import get_json_file, load_downloaded_urls

from .logger import get_logger
from .get_download import get_download
from .db import pdf_exists, save_pdf

logger = get_logger("amfi")

URL = "https://www.amfiindia.com/distributor/amfi-circulars"
BASE_URL = "https://www.amfiindia.com"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/137.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9"
}

ALLOWED_EXTENSIONS = (".pdf", ".doc", ".docx", ".xls", ".xlsx", ".zip", ".csv")


def normalize_url(href, base_url):
    href = href.strip()
    if href.startswith("/"):
        href = base_url.rstrip("/") + href
    return urljoin(base_url, href)


def generic_document_extractor(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    links = []

    for tag in soup.find_all("a", href=True):
        href = normalize_url(tag["href"], base_url)

        if href.lower().endswith(ALLOWED_EXTENSIONS):
            links.append(href)

    return list(dict.fromkeys(links))


def extract_amfi(html, base_url):
    logger.info("Running AMFI extractor...")
    return generic_document_extractor(html, base_url)


def fetch_html():
    response = requests.get(URL, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.text


def generate_filename(document_url):
    original_filename = document_url.split("/")[-1]
    url_hash = hashlib.md5(document_url.encode("utf-8")).hexdigest()[:8]
    base, ext = os.path.splitext(original_filename)
    return f"{base}_{url_hash}{ext}"


def download_documents(document_links, download_folder):
    downloaded = 0
    failed = 0

    for document_url in document_links:

        filename = generate_filename(document_url)
        filepath = os.path.join(download_folder, filename)

        try:
            logger.info(f"Downloading : {filename}")

            response = requests.get(
                document_url,
                headers=HEADERS,
                timeout=60
            )
            response.raise_for_status()

            with open(filepath, "wb") as file:
                file.write(response.content)

            save_pdf(
                source="AMFI",
                pdf_name=filename,
                pdf_link=document_url,
                category="Circulars"
            )

            downloaded += 1

        except Exception:
            logger.exception(f"Failed : {filename}")
            failed += 1

    return downloaded, failed


def download_amfi():
    logger.info("")
    logger.info("========== AMFI ==========")

    download_folder = get_download("amfi")

    html = fetch_html()
    document_links = extract_amfi(html, BASE_URL)

    total = len(document_links)

    new_documents = []

    for url in document_links:

        filename = generate_filename(url)

        if pdf_exists("AMFI", filename):
            logger.info(f"{filename} already exists in database.")
            continue

        new_documents.append(url)

    already_processed = total - len(new_documents)

    logger.info(f"Total Documents Found : {total}")
    logger.info(f"Already Processed     : {already_processed}")

    if not new_documents:
        logger.info("No new documents found.")
        return

    downloaded, failed = download_documents(
        new_documents,
        download_folder
    )

    logger.info("")
    logger.info("AMFI Summary")
    logger.info("-------------------------")
    logger.info(f"Total Documents Found : {total}")
    logger.info(f"Already Processed     : {already_processed}")
    logger.info(f"Downloaded            : {downloaded}")
    logger.info(f"Failed                : {failed}")