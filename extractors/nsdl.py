import requests
from datetime import datetime

from .db import save_pdf, pdf_exists
from .helpers import (
    get_logger,
    load_seen,
    save_seen,
    download_pdf,
    safe_filename,
    dest_for,
)

MONTH_API = "https://nsdl.com/web/api/v1/circular/month-list"
PDFLIST_API = "https://nsdl.com/web/api/v1/circular/typewise/pdflist"

YEAR = str(datetime.now().year)

TYPES = {
    "DP": "participant-circular-dp",
    "Issuers & RTAs": "participant-circular-issuer-rta",
    "Master Circular": "master-circular",
}


def scrape_nsdl() -> tuple[int, int]:
    log = get_logger("nsdl")
    seen = load_seen("nsdl")

    found = 0
    downloaded = 0

    session = requests.Session()

    today = datetime.now().strftime("%d %B %Y").lstrip("0")

    for category, type_value in TYPES.items():

        log.info("Processing %s...", category)

        # Master Circular doesn't use the month parameter
        if type_value == "master-circular":
            months = [None]
        else:
            try:
                r = session.get(
                    MONTH_API,
                    params={
                        "type": type_value,
                        "year": YEAR,
                    },
                    timeout=30,
                )
                r.raise_for_status()

                months = [m["month"] for m in r.json().get("data", [])]

            except Exception as e:
                log.error(
                    "Failed to fetch months for %s: %s",
                    category,
                    e,
                )
                continue

        for month in months:

            page = 0

            while True:

                params = {
                    "type": type_value,
                    "limit": 10,
                    "page": page,
                    "year": YEAR,
                }

                if month:
                    params["month"] = month

                try:
                    r = session.get(
                        PDFLIST_API,
                        params=params,
                        timeout=30,
                    )

                    r.raise_for_status()
                    data = r.json()

                except Exception as e:
                    log.error(
                        "Failed to fetch %s page %d: %s",
                        category,
                        page,
                        e,
                    )
                    break

                records = data.get("data", [])

                if not records:
                    break

                total_pages = data.get("total_pages", 1)

                for record in records:

                    # Master Circulars don't have daily dates
                    if month and record.get("date") != today:
                        continue

                    file_info = record.get("file")
                    if not file_info:
                        continue

                    file_url = file_info.get("file_url")
                    if not file_url:
                        continue

                    found += 1

                    if file_url in seen:
                        continue

                    ext = "." + file_info.get("extension", "").lower()

                    filename = (
                        safe_filename(record["pdf_title"])
                        + ext
                    )

                    if pdf_exists("NSDL", filename):
                        continue

                    dest = dest_for("NSDL", filename)

                    if download_pdf(file_url, dest, log):

                        save_pdf(
                            source="NSDL",
                            pdf_name=filename,
                            pdf_link=file_url,
                            category=category,
                        )

                        seen.add(file_url)
                        downloaded += 1

                page += 1

                if page >= total_pages:
                    break

    save_seen("nsdl", seen)

    log.info(
        "NSDL Complete → found %d files in database, downloaded %d new",
        found,
        downloaded,
    )

    return found, downloaded