
import hashlib
import os
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .get_download import get_download


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


ALLOWED_EXTENSIONS = (

    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".zip",
    ".csv"

)


def normalize_url(href, base_url):

    href = href.strip()

    if href.startswith("/"):

        href = base_url.rstrip("/") + href

    return urljoin(
        base_url,
        href
    )


def generic_document_extractor(
    html,
    base_url
):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    links = []

    for tag in soup.find_all(
        "a",
        href=True
    ):

        href = tag["href"]

        href = normalize_url(
            href,
            base_url
        )

        if not href.lower().endswith(
            ALLOWED_EXTENSIONS
        ):
            continue

        links.append(href)

    return list(
        dict.fromkeys(
            links
        )
    )


def extract_amfi(
    html,
    base_url
):

    print("Running AMFI extractor...")

    return generic_document_extractor(
        html,
        base_url
    )


def fetch_html():

    response = requests.get(
        URL,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    return response.text


def generate_filename(document_url):

    original_filename = document_url.split("/")[-1]

    url_hash = hashlib.md5(
        document_url.encode("utf-8")
    ).hexdigest()[:8]

    base, ext = os.path.splitext(
        original_filename
    )

    return f"{base}_{url_hash}{ext}"


def download_documents(
    document_links,
    download_folder
):

    downloaded = 0
    skipped = 0

    for document_url in document_links:

        filename = generate_filename(
            document_url
        )

        filepath = os.path.join(
            download_folder,
            filename
        )

        if os.path.exists(filepath):

            print(f"[EXISTS] {filename}")

            skipped += 1

            continue

        try:

            print(f"Downloading : {filename}")

            response = requests.get(
                document_url,
                headers=HEADERS,
                timeout=60
            )

            response.raise_for_status()

            with open(filepath, "wb") as file:

                file.write(
                    response.content
                )

            downloaded += 1

        except Exception as e:

            print(f"Failed : {filename}")

            print(e)

    print("\nAMFI Summary")
    print("------------------------")
    print(f"Downloaded : {downloaded}")
    print(f"Skipped    : {skipped}")


def download_amfi():

    print("\n========== AMFI ==========")

    html = fetch_html()

    document_links = extract_amfi(
        html,
        BASE_URL
    )

    print(
        f"Found {len(document_links)} document(s)"
    )

    if not document_links:

        print("No documents found.")

        return

    download_folder = get_download(
        "amfi"
    )

    download_documents(
        document_links,
        download_folder
    )

    print("AMFI Completed.")