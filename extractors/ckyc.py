import hashlib
import os
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .logger import get_logger
from .helpers import load_seen, save_seen, dest_for, download_pdf
from .db import pdf_exists, save_pdf

logger = get_logger("ckcy")
URL = "https://www.ckycindia.in/ckyc/?r=notification"
BASE_URL = "https://www.ckycindia.in"

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


def extract_ckyc(html, base_url):
    logger.info("Running CKYC extractor...")
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


def download_documents(document_links, seen):
    downloaded = 0
    failed = 0
    broken = 0

    for document_url in document_links:

        filename = generate_filename(document_url)
        dest = dest_for("CKYC", filename)

        logger.info(f"Downloading : {filename}")
        try:
            head = requests.head(
                document_url,
                headers=HEADERS,
                timeout=30,
                allow_redirects=True
            )
            if head.status_code == 404:
                logger.warning(f"Broken document link (404): {document_url}")
                broken += 1
                continue
        except requests.RequestException:
            pass

        if not download_pdf(document_url, dest, logger):
            failed += 1
            continue

        save_pdf(
            source="CKYC",
            pdf_name=filename,
            pdf_link=document_url,
            category="Circulars"
        )

        seen.add(document_url)
        downloaded += 1

    return downloaded, failed, broken


def download_ckyc():
    logger.info("")
    logger.info("========== CKYC ==========")

    seen = load_seen("ckyc")

    html = fetch_html()
    document_links = extract_ckyc(html, BASE_URL)

    total = len(document_links)

    new_documents = []

    for url in document_links:

        filename = generate_filename(url)

        if pdf_exists("CKYC", filename):
            # logger.info(f"{filename} already exists in database.")
            continue

        new_documents.append(url)

    already_processed = total - len(new_documents)
    logger.info(f"Total Documents Found : {total}")
    logger.info(f"Already Processed     : {already_processed}")

    if not new_documents:
        logger.info("No new documents found.")
        save_seen("ckyc", seen)
        return

    downloaded, failed, broken = download_documents(new_documents, seen)

    save_seen("ckyc", seen)

    logger.info("")
    logger.info("CKYC Summary")
    logger.info("-------------------------")
    logger.info(f"Total Documents Found : {total}")
    logger.info(f"Already Processed     : {already_processed}")
    logger.info(f"Downloaded            : {downloaded}")
    logger.info(f"Broken Links (404)    : {broken}")
    logger.info(f"Failed                : {failed}")
