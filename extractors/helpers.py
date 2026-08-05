import re
import sys
import json
import logging
import urllib3
from datetime import date
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from .config import (
    BASE_DOWNLOAD_DIR,
    LOG_DIR,
    SEEN_DIR,
    REQUEST_TIMEOUT,
    HEADERS,
)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# ──────────────────────────────────────────────
# LOGGING
# ──────────────────────────────────────────────
def get_logger(site_name: str):

    logger = logging.getLogger(site_name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)-8s %(message)s"
    )

    logfile = LOG_DIR / f"{site_name.lower()}_log.log"

    file_handler = logging.FileHandler(
        logfile,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def get_seen_file(site_name: str):
    return SEEN_DIR / f"{site_name.lower()}_seen.json"


def load_seen(site_name: str):

    db_file = get_seen_file(site_name)

    if db_file.exists():
        try:
            with open(db_file, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception:
            pass

    return set()


def save_seen(site_name: str, seen: set):

    db_file = get_seen_file(site_name)

    with open(db_file, "w", encoding="utf-8") as f:
        json.dump(sorted(seen), f, indent=2)
# ══════════════════════════════════════════════
# HTTP HELPERS
# ══════════════════════════════════════════════

def get_page(url: str,log) -> BeautifulSoup | None:
    """Fetch a web page and return a BeautifulSoup object, or None on error."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "lxml")
    except requests.RequestException as exc:
        log.error("Failed to fetch page %s  →  %s", url, exc)
        return None


def download_pdf(url: str, dest_path: Path, log, session=None,
                  extra_headers=None, _verify=True) -> bool:
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    req_headers = dict(HEADERS)
    if extra_headers:
        req_headers.update(extra_headers)

    requester = session if session is not None else requests

    try:
        with requester.get(url, headers=req_headers, timeout=REQUEST_TIMEOUT,
                            stream=True, verify=_verify) as resp:
            resp.raise_for_status()
            with open(dest_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
        log.info("  ✔  Saved  %s", dest_path)
        return True
    except requests.exceptions.SSLError as exc:
        if _verify:
            log.warning(
                " SSL verification failed for %s (%s). "
                "Retrying without verification.", url, exc
            )
            return download_pdf(url, dest_path, log, session=session,
                                 extra_headers=extra_headers, _verify=False)
        log.error("  ✘  Download failed  %s  →  %s", url, exc)
        if dest_path.exists():
            dest_path.unlink()
        return False
    except requests.RequestException as exc:
        log.error("  ✘  Download failed  %s  →  %s", url, exc)
        # remove partial file if it exists
        if dest_path.exists():
            dest_path.unlink()
        return False


def safe_filename(name: str) -> str:
    """Strip characters that are unsafe in file/folder names."""
    name = re.sub(r'[\\/*?:"<>|]', "_", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name[:200]          # cap length


def dest_for(source_name: str, filename: str) -> Path:
    today = date.today().isoformat()
    return BASE_DOWNLOAD_DIR / source_name / today / filename