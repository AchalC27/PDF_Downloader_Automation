from pathlib import Path
from urllib.parse import urljoin, urlparse

from .db import save_pdf, pdf_exists

from .helpers import (
    get_logger,
    get_page,
    safe_filename,
    dest_for,
    download_pdf,
)

APMI_BASE = "https://www.apmiindia.org"
APMI_HOME = "https://www.apmiindia.org/apmi/welcome.htm"


def extract_pdf_links(node, pdf_links):
    if node.name == "a" and node.has_attr("href"):
        href = urljoin(APMI_HOME, node["href"].strip())

        if href.lower().endswith(".pdf"):
            pdf_links.add(href)

    for child in node.children:
        if getattr(child, "name", None):
            extract_pdf_links(child, pdf_links)


def get_apmi_pdf_links(soup):
    pdf_links = set()

    # Step 1: Find the CIRCULARS menu
    circulars_li = None

    for li in soup.find_all("li"):
        a = li.find("a", recursive=False)

        if a and a.get_text(strip=True).upper() == "CIRCULARS":
            circulars_li = li
            break

    if circulars_li is None:
        return pdf_links

    TARGET_MENUS = {
        "SEBI Circulars",
        "Communication from SEBI",
        "SEBI Consultation Papers",
        "SEBI Board Meetings",
        "APMI Circulars and Guidelines",
        "Communication from APMI",
    }

    # Step 2: Process ALL matching menus
    for li in circulars_li.find_all("li"):
        a = li.find("a", recursive=False)

        if not a:
            continue

        text = a.get_text(strip=True)

        if text in TARGET_MENUS:
            logger = get_logger("apmi")
            logger.info("Processing: %s", text)
            extract_pdf_links(li, pdf_links)

    return pdf_links


def scrape_apmi() -> tuple[int, int]:
    log = get_logger("apmi")

    log.info("─── Scraping APMI ───")

    soup = get_page(APMI_HOME, log)

    if soup is None:
        return 0, 0

    pdf_links = get_apmi_pdf_links(soup)

    if not pdf_links:
        log.warning("No PDF links found.")
        return 0, 0

    found = 0
    downloaded = 0

    for pdf_url in sorted(pdf_links):

        found += 1

        filename = safe_filename(
            Path(urlparse(pdf_url).path).name
        )

        if pdf_exists("APMI", filename):
            # log.info("%s already exists in database. Skipping.", filename)
            continue

        dest = dest_for("APMI", filename)

        log.info("Saving %s", filename)

        if not download_pdf(pdf_url, dest, log):
            continue

        save_pdf(
            source="APMI",
            pdf_name=filename,
            pdf_link=pdf_url,
            category="Circular",
        )

        downloaded += 1

    log.info(
        "APMI -> Found %d PDFs, Saved %d",
        found,
        downloaded,
    )

    return found, downloaded