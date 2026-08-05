import os

DB_HOST = os.environ.get("DASH_DB_HOST", "localhost")
DB_USER = os.environ.get("DASH_DB_USER", "root")
DB_PASSWORD = os.environ.get("DASH_DB_PASSWORD", "sunnamrev04")
DB_NAME = os.environ.get("DASH_DB_NAME", "file_downloader")

DASHBOARD_HOST = os.environ.get("DASH_HOST", "0.0.0.0")
DASHBOARD_PORT = int(os.environ.get("DASH_PORT", "5001"))
DASHBOARD_DEBUG = os.environ.get("DASH_DEBUG", "1") == "1"

# Known extractor sources (used as fallback list + colour assignment order).
KNOWN_SOURCES = [
    "NSE", "BSE", "CDSL", "AMFI", "ARCL", "CKYC",
    "MCX", "APMI", "PFRDA", "NSDL", "SEBI", "IRDAI",
]
