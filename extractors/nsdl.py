from pathlib import Path
from urllib.parse import urljoin, urlparse
from .db import save_pdf, pdf_exists

from .helpers import (
    get_logger,
    load_seen,
    save_seen,
    get_page,
    download_pdf,
    safe_filename,
    dest_for,
)

NSDL_URL = "https://nsdl.co.in/business/circular_stat.php"
def scrape_nsdl() -> tuple[int, int]:
    """
    Scrape NSDL circulars page and download explicit PDF/DOC/DOCX/ZIP files.
    Uses exact string matching to align perfectly with browser console counts.
    """
    log = get_logger("nsdl")
    seen = load_seen("nsdl")

    soup = get_page(NSDL_URL, log)
    if soup is None:
        return 0, 0

    found = 0
    downloaded = 0

    # Isolate the exact table container using your verified CSS selector path
    target_selector = "body > div > div.row.mb-5.mb-md-10 > div.col-sm-12.col-xs-12.col-md-9.col-lg-9.text-left.right-panel.mt-3 > table"
    target_table = soup.select_one(target_selector)

    if target_table is None:
        log.error("Could not find the target table on the page using the specified selector.")
        return 0, 0

    # Loop through every link inside the isolated table structure
    for a_tag in target_table.find_all("a", href=True):
        href = a_tag["href"].strip()
        
        # Skip baseline empty anchor links or javascript macros
        if not href or href.startswith(("#", "javascript:")):
            continue

        full_url = urljoin(NSDL_URL, href)
        
        # Lowercase the entire URL string for direct suffix evaluation
        url_lower = full_url.lower()

        # Replicate the exact console matching behavior
        if url_lower.endswith(".pdf"):
            ext = ".pdf"
        elif url_lower.endswith(".zip"):
            ext = ".zip"
        elif url_lower.endswith(".docx"):
            ext = ".docx"
        elif url_lower.endswith(".doc"):
            ext = ".doc"
        else:
            # If it doesn't match our exact extension strings, skip it
            continue

        found += 1

        if full_url in seen:
            continue

        link_text = a_tag.get_text(" ", strip=True)

        # Generate a clean system filename
        if link_text:
            filename = safe_filename(link_text) + ext
        else:
            # Fallback parsing if link text is missing
            path_stem = urlparse(full_url).path.split('/')[-1].rsplit('.', 1)[0]
            filename = safe_filename(path_stem or f"nsdl_document_{found}") + ext

        if pdf_exists("NSDL", filename):
                log.info("%s already exists in database. Skipping.", filename)
                continue
        dest = dest_for("NSDL", filename)

        # Attempt download execution
        if download_pdf(full_url, dest, log):
            save_pdf(
                source="NSDL",
                pdf_name=filename,
                pdf_link=full_url,
                category="Circular"
            )
            seen.add(full_url)
            downloaded += 1

    save_seen("nsdl", seen)

    log.info(
        "NSDL Complete → found %d files, downloaded %d new",
        found,
        downloaded
    )
    
    return found, downloaded