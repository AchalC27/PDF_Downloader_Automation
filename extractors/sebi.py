
from pathlib import Path
from urllib.parse import urljoin, urlparse, parse_qs
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


SEBI_URL = "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=1&ssid=7&smid=0"





def scrape_sebi() -> tuple[int, int]:
    """
    Scrape SEBI circular table and download PDFs.
    Handles both:
      1. Direct PDF links
      2. Detail pages containing PDF inside an iframe
    Returns (found, downloaded).
    """

    log = get_logger("sebi")
    seen = load_seen("sebi")

    soup = get_page(SEBI_URL, log)
    if soup is None:
        return 0, 0

    found = 0
    downloaded = 0

    rows = soup.find_all("tr")

    for row in rows:

        links = row.find_all("a", href=True)

        for a_tag in links:

            href = a_tag["href"].strip()

            if not href:
                continue

            full_url = urljoin(SEBI_URL, href)
            found += 1

            # Skip already processed detail page
            if full_url in seen:
                continue

            title = a_tag.get_text(" ", strip=True)

            # ----------------------------------------------------
            # CASE 1 : Direct PDF
            # ----------------------------------------------------
            if full_url.lower().endswith(".pdf"):
                pdf_url = full_url

            # ----------------------------------------------------
            # CASE 2 : Open detail page and extract iframe PDF
            # ----------------------------------------------------
            else:

                detail_soup = get_page(full_url, log)

                if detail_soup is None:
                    continue

                iframe = detail_soup.find("iframe")

                if iframe is None:
                    log.info("No iframe found on %s", full_url)
                    continue

                iframe_src = iframe.get("src", "").strip()

                if not iframe_src:
                    log.info("Iframe has no src on %s", full_url)
                    continue

                iframe_url = urljoin(full_url, iframe_src)

                # iframe URL:
                # /web/?file=https://www.sebi.gov.in/sebi_data/attachdocs/...pdf

                parsed = urlparse(iframe_url)
                params = parse_qs(parsed.query)

                if "file" in params:
                    pdf_url = params["file"][0]
                else:
                    pdf_url = iframe_url

            # ----------------------------------------------------
            # Skip if PDF already downloaded
            # ----------------------------------------------------
            if pdf_url in seen:
                continue

            # ----------------------------------------------------
            # Filename
            # ----------------------------------------------------
            filename = Path(urlparse(pdf_url).path).name

            if not filename.lower().endswith(".pdf"):

                if title:
                    filename = safe_filename(title) + ".pdf"
                else:
                    filename = f"sebi_{found}.pdf"
            
            if pdf_exists("SEBI", filename):
                log.info("%s already exists in database. Skipping.", filename)
                continue

            dest = dest_for("SEBI", filename)

            # ----------------------------------------------------
            # Download
            # ----------------------------------------------------
            if download_pdf(pdf_url, dest, log):
                save_pdf(
                source="SEBI",
                pdf_name=filename,
                pdf_link=pdf_url,
                category="Circular"
                )
                seen.add(full_url)
                seen.add(pdf_url)
                downloaded += 1

                log.info("Downloaded: %s", filename)

    save_seen("sebi", seen)

    log.info(
        "SEBI → found %d circulars, downloaded %d new",
        found,
        downloaded,
    )

    return found, downloaded