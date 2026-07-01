
import argparse
import schedule
import time
from datetime import datetime

from extractors.logger import get_logger
from extractors.config import BASE_DOWNLOAD_DIR, SCHEDULE_TIME

from extractors.nse import download_nse
from extractors.bse import download_bse
from extractors.cdsl import download_cdsl
from extractors.amfi import download_amfi
from extractors.arcl import download_arcl
from extractors.ckyc import download_ckyc
from extractors.mcx import download_mcx
from extractors.apmi import scrape_apmi
from extractors.pfrda import scrape_pfrda
from extractors.nsdl import scrape_nsdl
from extractors.sebi import scrape_sebi
from extractors.irdai import scrape_irdai


logger = get_logger("master")


WEBSITES = [

    # ("NSE", download_nse),
    # ("BSE", download_bse),
    # ("CDSL", download_cdsl),
    # ("AMFI", download_amfi),
    # ("ARCL", download_arcl),
    ("CKYC", download_ckyc),
    # ("MCX", download_mcx),

    # ("APMI", scrape_apmi),
    # ("PFRDA", scrape_pfrda),
    # ("NSDL", scrape_nsdl),
    # ("SEBI", scrape_sebi),
    # ("IRDAI", scrape_irdai),

]


def run_website(name, function):

    logger.info("─" * 60)
    logger.info("Running %s", name)

    try:

        function()

        logger.info("%s Completed Successfully", name)

    except Exception:

        logger.exception("%s Failed", name)


def run_once():

    start = datetime.now()

    logger.info("═" * 60)
    logger.info(
        "Scraping run started at %s",
        start.strftime("%Y-%m-%d %H:%M:%S")
    )
    logger.info("═" * 60)

    for name, function in WEBSITES:

        run_website(name, function)

    elapsed = (datetime.now() - start).total_seconds()

    logger.info("─" * 60)
    logger.info("Summary")
    logger.info("")
    logger.info(
        "Run completed in %.1f seconds",
        elapsed
    )
    logger.info(
        "Downloads saved under: %s",
        BASE_DOWNLOAD_DIR.resolve()
    )
    logger.info("═" * 60)
    logger.info("")


def main():

    parser = argparse.ArgumentParser(
        description="PDF Downloader Automation"
    )

    parser.add_argument(
        "--loop",
        action="store_true",
        help=f"Run every day at {SCHEDULE_TIME}"
    )

    args = parser.parse_args()

    if args.loop:

        logger.info(
            "Scheduler started at %s",
            SCHEDULE_TIME
        )

        run_once()

        schedule.every().day.at(
            SCHEDULE_TIME
        ).do(run_once)

        while True:

            schedule.run_pending()

            time.sleep(60)

    else:

        run_once()
if __name__ == "__main__":
    main()

