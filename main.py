

from datetime import datetime

from extractors.nse import download_nse
from extractors.bse import download_bse
from extractors.cdsl import download_cdsl
from extractors.amfi import download_amfi
from extractors.arcl import download_arcl
from extractors.ckyc import download_ckyc
from extractors.mcx import download_mcx


def run(name, function):
    print("\n" + "=" * 60)
    print(f"Running {name}")
    print("=" * 60)

    try:
        function()

        print(f"{name} Completed Successfully")

    except Exception as e:
        print(f"{name} Failed")
        print(e)


def main():

    print("\n")
    print("=" * 70)
    print("PDF AUTOMATION SYSTEM")
    print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"))
    print("=" * 70)

    run("NSE", download_nse)

    run("BSE", download_bse)

    run("CDSL", download_cdsl)

    run("AMFI", download_amfi)

    run("ARCL", download_arcl)

    run("CKYC", download_ckyc)

    run("MCX", download_mcx)

    print("\n")
    print("=" * 70)
    print("Automation Finished")
    print("=" * 70)


if __name__ == "__main__":
    main()