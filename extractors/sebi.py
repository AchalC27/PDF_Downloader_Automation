
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


SEBI_URL = "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=1&ssid=7&smid=0"



def scrape_sebi() -> tuple[int, int]:
    """
    Scrape SEBI circular table and download files linked from the table.
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

            if full_url in seen:
                continue

            filename = Path(
                urlparse(full_url).path
            ).name

            if not filename:
                link_text = a_tag.get_text(strip=True)

                if link_text:
                    filename = safe_filename(link_text)
                else:
                    filename = f"sebi_file_{found}"

            dest = dest_for("SEBI", filename)

            if download_pdf(full_url, dest, log):
                seen.add(full_url)
                downloaded += 1

    log.info(
        "SEBI → found %d table links, downloaded %d new",
        found,
        downloaded
    )

    save_seen("sebi", seen)

    return found, downloaded

    