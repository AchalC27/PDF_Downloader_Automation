from pathlib import Path
from urllib.parse import urljoin, urlparse
import re
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

IRDAI_URL="https://irdai.gov.in/circulars?p_p_id=com_irdai_document_media_IRDAIDocumentMediaPortlet&p_p_lifecycle=0&p_p_state=normal&p_p_mode=view&_com_irdai_document_media_IRDAIDocumentMediaPortlet_filterEntities=WEB_AGGREGATORS&_com_irdai_document_media_IRDAIDocumentMediaPortlet_resetCur=false&_com_irdai_document_media_IRDAIDocumentMediaPortlet_delta=20"
def scrape_irdai() -> tuple[int, int]:
    """
    Scrape IRDAI circulars page and download any new PDFs.
    Returns (found, downloaded) counts.
    """
    log = get_logger("irdai")
    seen = load_seen("irdai")

    soup = get_page(IRDAI_URL, log)
    if soup is None:
        return 0, 0

    found = downloaded = 0

    # Find all circular containers
    containers = soup.find_all(
        "div",
        class_="col-lg-8 col-md-8 col-sm-8 col-8"
    )
    
    for container in containers:
        for a_tag in container.find_all("a", href=True):
            href = a_tag["href"].strip()
            full_url = urljoin(IRDAI_URL, href)

            found += 1

            if full_url in seen:
                continue

            link_text = a_tag.get_text(" ", strip=True)

            # Remove Hindi (and any other non-ASCII) characters
            link_text = re.sub(r'[^\x00-\x7F]+', '', link_text)

            # Remove extra spaces left after removing Hindi
            link_text = " ".join(link_text.split())

            ext = Path(urlparse(full_url).path).suffix.lower()

            if link_text:
                filename = safe_filename(link_text) + ext
            else:
                filename = safe_filename(Path(urlparse(full_url).path).name)
            
            if pdf_exists("IRDAI", filename):
                # log.info("%s already exists in database. Skipping.", filename)
                continue

            dest = dest_for("IRDAI", filename)
            if download_pdf(full_url, dest, log):
                save_pdf(
                source="IRDAI",
                pdf_name=filename,
                pdf_link=full_url,
                category="Circular"
                )
                seen.add(full_url)
                downloaded += 1

    log.info(
        "IRDAI → found %d PDF links, downloaded %d new",
        found,
        downloaded,
    )

    save_seen("irdai", seen)
    return found, downloaded