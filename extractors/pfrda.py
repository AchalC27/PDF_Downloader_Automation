from pathlib import Path
from urllib.parse import urljoin, urlparse

from .db import save_pdf, pdf_exists
from .helpers import (
    get_logger,
    load_seen,
    save_seen,
    get_page,
    safe_filename,
    dest_for,
    download_pdf,
)

PFRDA_URL = "https://pfrda.org.in/regulatory-framework/circulars/active-circulars"


def scrape_pfrda() -> tuple[int, int]:
    """
    Scrape the first 3 pages of PFRDA active circulars.
    Save only metadata to MySQL.
    Returns (found, saved).
    """

    log = get_logger("pfrda")
    seen = load_seen("pfrda")

    log.info("─── Scraping PFRDA ───")

    found = 0
    saved = 0

    soup = get_page(PFRDA_URL, log)

    if soup is None:
        return 0, 0

    pages = 3

    for page in range(1, pages + 1):

        if page == 1:
            page_soup = soup
        else:
            page_url = f"{PFRDA_URL}?delta=10&start={page}"

            log.info("Opening %s", page_url)

            page_soup = get_page(page_url, log)

            if page_soup is None:
                continue

        cards = page_soup.find_all("div", class_="basic-card")

        log.info("Page %d : %d cards", page, len(cards))

        for card in cards:
            a = card.find("a", class_="basic-link", href=True)

            if a is None:
                continue

            detail_url = urljoin(PFRDA_URL, a["href"])

            title = a.get_text(" ", strip=True)

            detail_soup = get_page(detail_url, log)

            if detail_soup is None:
                continue

            pdf_url = None

            for link in detail_soup.find_all("a", href=True):

                href = urljoin(detail_url, link["href"])

                if ".pdf" in href.lower():
                    pdf_url = href
                    break

            if pdf_url is None:
                continue

            found += 1

            if pdf_url in seen:
                continue

            filename = safe_filename(title)

            ext = Path(urlparse(pdf_url).path).suffix.lower()

            if not ext:
                ext = ".pdf"

            filename += ext

            if pdf_exists("PFRDA", filename):
                continue

            try:
                dest = dest_for("PFRDA", filename)

                if not download_pdf(pdf_url, dest, log):
                    continue

                save_pdf(
                    source="PFRDA",
                    pdf_name=filename,
                    pdf_link=pdf_url,
                    category="Circular",
                )

                saved += 1
                seen.add(pdf_url)

                log.info("Saved : %s", filename)

            except Exception:
                log.exception("Failed : %s", filename)

    save_seen("pfrda", seen)

    log.info(
        "PFRDA → Found %d PDFs, Saved %d",
        found,
        saved,
    )

    return found, saved