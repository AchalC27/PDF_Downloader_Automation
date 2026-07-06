import re
from datetime import datetime
from urllib.parse import unquote
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import requests

from .logger import get_logger
from .get_download import get_download
from .db import pdf_exists, save_pdf

logger = get_logger("cdsl")

BASE_URL = "https://www.cdslindia.com"
PAGE_URL = f"{BASE_URL}/eservices/Publications/Communique"
# API_URL = f"{BASE_URL}/eservices/Publications/GetOnLoadCommunique"
DOWNLOAD_URL = f"{BASE_URL}/eservices/Publications/DownloadFile"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": PAGE_URL,
}

# SEARCH_PROFILES = [
#     {
#         "label": "DP",
#         "payload": {
#             "m_arch_status": "A",
#             "type": "3",
#             "cno": "DP%",
#             "fromDate": "01-Jan-1990",
#             "toDate": "",
#             "Keyword": "%",
#             "Subject": "%",
#             "GCaptcha": "%",
#         },
#     },
#     {
#         "label": "RTA",
#         "payload": {
#             "m_arch_status": "A",
#             "type": "4",
#             "cno": "RTA%",
#             "fromDate": "01-Jan-1990",
#             "toDate": "",
#             "Keyword": "%",
#             "Subject": "%",
#             "GCaptcha": "%",
#         },
#     },
# ]

DATE_FORMAT = "%d-%b-%Y"


def fetch_communiques(session):
    response = session.get(PAGE_URL, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    table = soup.find("tbody", id="tblCommuniquDtlBody")

    if table is None:
        logger.error("Communique table not found.")
        return []

    items = []

    for row in table.find_all("tr"):
        cols = row.find_all("td")

        if len(cols) < 4:
            continue

        comm_id = cols[0].get_text(strip=True)

        link = cols[1].find("a")

        subject = link.get_text(" ", strip=True)

        href = link.get("href", "")

        date = cols[3].get_text(strip=True)

        department = cols[2].get_text(strip=True)

        items.append(
            {
                "id": comm_id,
                "date": date,
                "subject": subject,
                "attachment": urljoin(BASE_URL, href),
                "label": department or "General",
            }
        )

    return items


def sanitize_filename(name):
    return re.sub(r'[<>:"/\\|?*]', "_", name)


def expected_filename(item):
    if item["attachment"]:
        name = unquote(item["attachment"]).replace("\\", "/").split("/")[-1]
    else:
        name = f'{item["id"]}.pdf'

    return sanitize_filename(name)


def get_filename(response, item):
    content = response.headers.get("Content-Disposition", "")
    match = re.search(r'filename\*?=(?:UTF-8\'\')?"?([^";]+)"?', content)

    if match:
        name = unquote(match.group(1)).replace("\\", "/").split("/")[-1]
        return sanitize_filename(name)

    return expected_filename(item)


def download_file(session, item, folder):
    url = item["attachment"]

    response = session.get(url, stream=True, timeout=60)
    response.raise_for_status()

    filename = get_filename(response, item)
    filepath = folder / filename

    if filepath.exists():
        stem, suffix, i = filepath.stem, filepath.suffix, 1
        while filepath.exists():
            filepath = folder / f"{stem}_{i}{suffix}"
            i += 1

    with open(filepath, "wb") as file:
        for chunk in response.iter_content(8192):
            if chunk:
                file.write(chunk)

    return url, filepath.name


def download_cdsl():
    logger.info("")
    logger.info("========== CDSL ==========")

    folder = get_download("cdsl")

    session = requests.Session()
    session.headers.update(HEADERS)

    try:
        session.get(PAGE_URL, timeout=20)
    except Exception:
        pass

    items = fetch_communiques(session)

    today = datetime.now().strftime(DATE_FORMAT)
    items = [item for item in items if item["date"] == today]

    total = len(items)
    logger.info(f"Total Communiques Found : {total}")

    new_items = []
    already_processed = 0

    for item in items:
        filename = expected_filename(item)

        if pdf_exists("CDSL", filename):
            already_processed += 1
            continue

        new_items.append(item)

    logger.info(f"Already Processed       : {already_processed}")

    if not new_items:
        logger.info("No new communiques found.")
        return

    downloaded = 0
    failed = 0

    for item in new_items:
        try:
            url, filename = download_file(session, item, folder)

            save_pdf(
                source="CDSL",
                pdf_name=filename,
                pdf_link=url,
                category=item["label"],
            )

            logger.info(f"Downloaded : {filename}")
            downloaded += 1

        except Exception:
            failed += 1
            logger.exception(f"Failed : {item['id']}")

    logger.info("")
    logger.info("CDSL Summary")
    logger.info("-------------------------")
    logger.info(f"Total Communiques Found : {total}")
    logger.info(f"Already Processed       : {already_processed}")
    logger.info(f"Downloaded              : {downloaded}")
    logger.info(f"Failed                  : {failed}")