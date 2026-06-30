from pathlib import Path
from urllib.parse import urljoin, urlparse

from .helpers import (
    get_logger,
    load_seen,
    save_seen,
    get_page,
    download_pdf,
    safe_filename,
    dest_for,
)


# ══════════════════════════════════════════════
# SCRAPER  2 – APMI  (Circulars + SEBI Circulars)
# URL: https://www.apmiindia.org/apmi/welcome.htm
# The circulars live inside the "CIRCULARS" nav menu:
#   • SEBI Circulars
#   • APMI Circulars and Guidelines
#   • Communication from SEBI / APMI
# ══════════════════════════════════════════════

APMI_BASE = "https://www.apmiindia.org"
APMI_HOME = "https://www.apmiindia.org/apmi/welcome.htm"



def extract_pdf_links(node, pdf_links):
    """
    Recursively traverse the menu and collect all PDF URLs.
    """
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
            print(f"Processing: {text}")
            extract_pdf_links(li, pdf_links)

    return pdf_links

def scrape_apmi() -> tuple[int, int]:
    log = get_logger("apmi")
    seen = load_seen("apmi")

    log.info("─── Scraping APMI ───")

    soup = get_page(APMI_HOME, log)
    if soup is None:
        return 0, 0

    pdf_links = get_apmi_pdf_links(soup)

    if not pdf_links:
        log.warning("No PDF links found.")
        return 0, 0

    found = downloaded = 0

    for pdf_url in sorted(pdf_links):

        found += 1

        if pdf_url in seen:
            continue

        filename = safe_filename(Path(urlparse(pdf_url).path).name)
        dest = dest_for("APMI", filename)

        log.info("Downloading %s", filename)

        if download_pdf(pdf_url, dest, log):
            seen.add(pdf_url)
            downloaded += 1

    save_seen("apmi", seen)

    log.info("APMI -> Found %d PDFs, Downloaded %d", found, downloaded)

    return found, downloaded