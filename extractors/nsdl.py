import requests
from pathlib import Path

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

TYPE = "participant-circular-dp"
YEAR = "2026"


def scrape_nsdl() -> tuple[int, int]:

    log = get_logger("nsdl")
    seen = load_seen("nsdl")

    found = 0
    downloaded = 0

    session = requests.Session()

    # -------------------------
    # Get all months for 2026
    # -------------------------
    try:
        r = session.get(
            MONTH_API,
            params={
                "type": TYPE,
                "year": YEAR,
            },
            timeout=30,
        )
        r.raise_for_status()

        months = [m["month"] for m in r.json()["data"]]

    except Exception as e:
        log.error("Failed to fetch months: %s", e)
        return 0, 0

    # -------------------------
    # Iterate over every month
    # -------------------------
    for month in months:

        page = 0

        while True:

            try:
                r = session.get(
                    PDFLIST_API,
                    params={
                        "type": TYPE,
                        "limit": 10,
                        "page": page,
                        "year": YEAR,
                        "month": month,
                    },
                    timeout=30,
                )

                r.raise_for_status()

                data = r.json()

            except Exception as e:
                log.error(
                    "Failed to fetch %s page %d : %s",
                    month,
                    page,
                    e,
                )
                break

            records = data.get("data", [])

            if not records:
                break

            total_pages = data.get("total_pages", 1)

            for record in records:

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
                    log.info(
                        "%s already exists in database.",
                        filename,
                    )
                    continue

                dest = dest_for("NSDL", filename)

                if download_pdf(file_url, dest, log):

                    save_pdf(
                        source="NSDL",
                        pdf_name=filename,
                        pdf_link=file_url,
                        category="Circular",
                    )

                    seen.add(file_url)
                    downloaded += 1

            page += 1

            if page >= total_pages:
                break

    save_seen("nsdl", seen)

    log.info(
        "NSDL Complete → found %d files, downloaded %d new",
        found,
        downloaded,
    )

    return found, downloaded