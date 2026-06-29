from datetime import datetime
from extractors.logger import logger
from extractors.nse import download_nse
from extractors.bse import download_bse
from extractors.cdsl import download_cdsl
from extractors.amfi import download_amfi
from extractors.arcl import download_arcl
from extractors.ckyc import download_ckyc
from extractors.mcx import download_mcx


def run(name, function):

    logger.info("=" * 70)
    logger.info(f"Running {name}")
    logger.info("=" * 70)

    try:

        function()

        logger.info(f"{name} Completed Successfully")

    except Exception:

        logger.exception(f"{name} Failed")


def main():

    logger.info("")
    logger.info("=" * 80)
    logger.info("PDF AUTOMATION SYSTEM")
    logger.info(f"Started At : {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}")
    logger.info("=" * 80)

    run("NSE", download_nse)

    run("BSE", download_bse)

    run("CDSL", download_cdsl)

    run("AMFI", download_amfi)

    run("ARCL", download_arcl)

    run("CKYC", download_ckyc)

    run("MCX", download_mcx)

    logger.info("")
    logger.info("=" * 80)
    logger.info("AUTOMATION FINISHED")
    logger.info(f"Finished At : {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()