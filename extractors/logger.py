import logging
from pathlib import Path


LOG_FOLDER = Path("logs")

LOG_FOLDER.mkdir(
    parents=True,
    exist_ok=True
)

LOG_FILE = LOG_FOLDER / "automation.log"


logging.basicConfig(

    level=logging.INFO,

    format="%(asctime)s | %(levelname)-8s | %(message)s",

    handlers=[

        logging.FileHandler(
            LOG_FILE,
            encoding="utf-8"
        ),

        logging.StreamHandler()

    ]
)

logger = logging.getLogger("PDF_Automation")