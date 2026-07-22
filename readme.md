# PDF Downloader Automation

Automated scraper suite that pulls daily regulatory circulars, notices, and
disclosures from major Indian financial market and regulatory websites, logs
them into a MySQL database, and surfaces them through a Flask dashboard.

Built for tracking regulatory updates across exchanges, depositories, KYC
registries, and regulators without manually checking a dozen websites every
day.

## Sources covered

| Source | Description |
|---|---|
| NSE | National Stock Exchange circulars |
| BSE | Bombay Stock Exchange circulars |
| CDSL | Central Depository Services notices |
| AMFI | Association of Mutual Funds in India circulars |
| ARCL | Asset Reconstruction Company circulars |
| CKYC | Central KYC Registry notices |
| MCX | Multi Commodity Exchange circulars |
| APMI | Association of Portfolio Managers in India circulars |
| PFRDA | Pension Fund Regulatory and Development Authority circulars |
| NSDL | National Securities Depository notices |
| SEBI | Securities and Exchange Board of India circulars |
| IRDAI | Insurance Regulatory and Development Authority circulars |

## How it works

1. Each source has a dedicated extractor in `extractors/` that scrapes the
   source's site (or, where available, its underlying JSON API) for the
   day's circulars/notices.
2. Every record found is checked against the MySQL `store_pdf` table via
   `pdf_exists()` to skip anything already catalogued.
3. New records are logged with `save_pdf()`, storing the source, PDF name,
   original link, category, and upload date — no local file storage
   required.
4. `main.py` runs all extractors in sequence and prints a per-source and
   overall summary (found / already processed / downloaded / failed).
5. The Flask dashboard (`dashboard/`) reads from the same table to give a
   searchable, filterable view of everything that's been catalogued, with
   CSV export and a manual entry form.

## Project structure

```
PDF_Downloader_Automation/
├── main.py                # Entry point — runs all extractors once, or on a daily schedule
├── schedular.py            # Standalone loop that re-runs main.py every 2 hours
├── requirements.txt         # Dependencies for the scraper suite
├── extractors/
│   ├── config.py           # Paths, request headers, timeouts, schedule time
│   ├── db.py                # MySQL connection, pdf_exists() / save_pdf()
│   ├── helpers.py           # Logging, seen-file cache, HTTP + filename utilities
│   ├── logger.py             # Per-source logger setup
│   ├── nse.py, bse.py, cdsl.py, amfi.py, arcl.py,
│   │   ckyc.py, mcx.py, apmi.py, pfrda.py, nsdl.py,
│   │   sebi.py, irdai.py     # One scraper per source
│   └── get_download.py, json_handler.py
├── seen/                   # Per-source JSON caches of already-seen items
└── dashboard/
    ├── app.py                # Flask app and API routes
    ├── config.py              # DB connection + dashboard settings (env-driven)
    ├── db.py                   # Query layer for the dashboard
    ├── templates/index.html    # Dashboard UI
    └── static/                 # CSS/JS for the dashboard
```

## Requirements

- Python 3.10+
- MySQL server, running and reachable
- A `store_pdf` table (see [Database setup](#database-setup))

## Installation

```bash
git clone https://github.com/AchalC27/PDF_Downloader_Automation.git
cd PDF_Downloader_Automation
pip install -r requirements.txt
pip install -r dashboard/requirements.txt
```

## Database setup

Create the database and table the scrapers and dashboard both write to:

```sql
CREATE DATABASE IF NOT EXISTS file_downloader;

USE file_downloader;

CREATE TABLE IF NOT EXISTS store_pdf (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    upload_date DATE NOT NULL,
    source      VARCHAR(50) NOT NULL,
    pdf_link    TEXT NOT NULL,
    pdf_name    VARCHAR(255) NOT NULL,
    category    VARCHAR(100),
    UNIQUE KEY uniq_source_pdf (source, pdf_name)
);
```

Set your MySQL credentials as environment variables before running the
dashboard (see [Configuration](#configuration)). The scraper side currently
reads its connection details from `extractors/db.py` — update the
`get_connection()` call there with your own host/user/password/database
before running it.

> **Note:** Do not commit real database credentials to the repository.
> Move any hardcoded values in `extractors/db.py` to environment variables
> (matching the pattern already used in `dashboard/config.py`) before making
> this repository public or sharing it.

## Configuration

The dashboard reads its settings from environment variables, with sensible
defaults for local development:

| Variable | Default | Description |
|---|---|---|
| `DASH_DB_HOST` | `localhost` | MySQL host |
| `DASH_DB_USER` | `root` | MySQL user |
| `DASH_DB_PASSWORD` | — | MySQL password |
| `DASH_DB_NAME` | `file_downloader` | MySQL database name |
| `DASH_HOST` | `0.0.0.0` | Host the Flask app binds to |
| `DASH_PORT` | `5001` | Port the Flask app binds to |
| `DASH_DEBUG` | `1` | Flask debug mode |

Scraper-side settings (download paths, request timeout, schedule time,
request headers) live in `extractors/config.py`.

## Usage

### Run all extractors once

```bash
python main.py
```

### Run on a daily schedule (in-process)

```bash
python main.py --loop
```

Runs immediately, then again every day at the time set by `SCHEDULE_TIME`
in `extractors/config.py`.

### Run on a fixed interval (external scheduler)

```bash
python schedular.py
```

Runs `main.py` as a subprocess every 2 hours, indefinitely.

### Launch the dashboard

```bash
cd dashboard
python app.py
```

Visit `http://localhost:5001` to search, filter, and export catalogued
records, or add one manually.

## Logs

Each extractor writes to its own log file under `logs/`
(e.g. `logs/nse_log.log`), in addition to console output, so a single
source's run history can be checked without digging through a combined log.

## License

No license specified yet — add one (e.g. MIT) if you intend to make this
project open source in the usual sense.