
from pathlib import Path
from urllib.parse import urljoin, urlparse, parse_qs
from .db import save_pdf, pdf_exists

from .helpers import (
    get_logger,
    get_page,
    download_pdf,
    safe_filename,
    dest_for,
)
SEBI_URL = "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=1&ssid=7&smid=0"
def scrape_sebi() -> tuple[int, int]:

    log = get_logger("sebi")
    # seen = load_seen("sebi")

    soup = get_page(SEBI_URL, log)
    if soup is None:
        return 0, 0

    found = 0
    downloaded = 0

    rows = soup.find_all("tr")

    for row in rows:

        links = row.find_all("a", href=True)

        for a_tag in links:

            href = a_tag.get("href", "").strip()

            if not href:
                continue

            full_url = urljoin(SEBI_URL, href)
            found += 1

            # Skip already processed detail page
            # if full_url in seen:
            #     continue

            # Extract only the visible title from the table
            title = " ".join(a_tag.stripped_strings)

            if full_url.lower().endswith(".pdf"):
                pdf_url = full_url

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

                parsed = urlparse(iframe_url)
                params = parse_qs(parsed.query)

                if "file" in params:
                    pdf_url = params["file"][0]
                else:
                    pdf_url = iframe_url

            # if pdf_url in seen:
            #     continue

            # Always use the table title as the filename
            if title:
                filename = safe_filename(title) 
            else:
                filename = Path(urlparse(pdf_url).path).name

            if pdf_exists("SEBI", filename):
                continue

            dest = dest_for("SEBI", filename)

            if download_pdf(pdf_url, dest, log):

                save_pdf(
                    source="SEBI",
                    pdf_name=filename,
                    pdf_link=pdf_url,
                    category="Circular",
                )

                # seen.add(full_url)
                # seen.add(pdf_url)

                downloaded += 1

                log.info("Downloaded: %s", filename)

    # save_seen("sebi", seen)

    log.info(
        "SEBI → found %d circulars, downloaded %d new",
        found,
        downloaded,
    )

    return found, downloaded