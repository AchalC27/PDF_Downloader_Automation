import re
from datetime import datetime
from urllib.parse import unquote
import requests
from .get_download import get_download
BASE_URL = "https://www.cdslindia.com"

PAGE_URL = f"{BASE_URL}/eservices/Publications/Communique"

API_URL = f"{BASE_URL}/eservices/Publications/GetOnLoadCommunique"

DOWNLOAD_URL = f"{BASE_URL}/eservices/Publications/DownloadFile"
HEADERS = {

    "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",

    "X-Requested-With":
        "XMLHttpRequest",

    "Referer":
        PAGE_URL
}
SEARCH_PROFILES = [

    {
        "label": "DP",

        "payload": {

            "m_arch_status": "A",
            "type": "3",
            "cno": "DP%",
            "fromDate": "01-Jan-1990",
            "toDate": "",
            "Keyword": "%",
            "Subject": "%",
            "GCaptcha": "%",
        }
    },

    {
        "label": "RTA",

        "payload": {

            "m_arch_status": "A",
            "type": "4",
            "cno": "RTA%",
            "fromDate": "01-Jan-1990",
            "toDate": "",
            "Keyword": "%",
            "Subject": "%",
            "GCaptcha": "%",
        }
    }
]
DATE_FORMAT = "%d-%b-%Y"
def fetch_communiques(session):

    items = []

    for profile in SEARCH_PROFILES:

        response = session.post(
            API_URL,
            data=profile["payload"],
            timeout=30
        )

        response.raise_for_status()

        rows = response.json()

        for row in rows:

            comm_id = row.get("comM_ID", "").strip()

            if not comm_id:
                continue

            items.append({

                "id": comm_id,

                "date": row.get("comM_DATE", "").strip(),

                "subject": (
                    row.get("subject")
                    or row.get("description")
                    or ""
                ).strip(),

                "attachment":
                    row.get("attachmenT_URL", ""),

                "label":
                    profile["label"]

            })

    return items


def get_filename(response, item):

    content = response.headers.get(
        "Content-Disposition",
        ""
    )
    match = re.search(
        r'filename\*?=(?:UTF-8\'\')?"?([^";]+)"?',
        content
    )

    if match:

        return (
            unquote(match.group(1))
            .replace("\\", "/")
            .split("/")[-1]
        )
    if item["attachment"]:
        return (
            unquote(item["attachment"])
            .replace("\\", "/")
            .split("/")[-1]
        )

    return f'{item["id"]}.pdf'


def download_file(session, item, folder):

    url = (
        f"{DOWNLOAD_URL}"
        f"?eventID={item['id']}"
        f"&method=communique"
    )

    response = session.get(
        url,
        stream=True,
        timeout=60
    )

    response.raise_for_status()

    filename = re.sub(
        r'[<>:"/\\|?*]',
        "_",
        get_filename(response, item)
    )

    filepath = folder / filename

    if filepath.exists():

        print(f"Already Exists : {filename}")

        return False

    with open(filepath, "wb") as f:

        for chunk in response.iter_content(8192):

            if chunk:

                f.write(chunk)

    print(f"Downloaded : {filename}")

    return True


def download_cdsl():

    print("\n========== CDSL ==========")

    folder = get_download("cdsl")

    session = requests.Session()

    session.headers.update(HEADERS)

    try:
        session.get(PAGE_URL, timeout=20)
    except Exception:
        pass

    items = fetch_communiques(session)

    today = datetime.now().strftime(DATE_FORMAT)

    items = [

        item

        for item in items

        if item["date"] == today

    ]

    print(f"Found {len(items)} communique(s)")

    downloaded = 0

    skipped = 0

    for item in items:

        try:

            if download_file(
                session,
                item,
                folder
            ):

                downloaded += 1

            else:

                skipped += 1

        except Exception as e:

            skipped += 1

            print(e)

    print("\nCDSL Summary")
    print("----------------------")
    print(f"Downloaded : {downloaded}")
    print(f"Skipped    : {skipped}")
    print(f"Folder     : {folder}")