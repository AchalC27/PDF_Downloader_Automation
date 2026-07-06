import re

with open("cdsl_page.html", encoding="utf-8") as f:
    html = f.read()

patterns = [
    r"Get[A-Za-z]+Communique",
    r"DownloadFile",
    r"/eservices/Publications/[^\"']+",
    r"\$.ajax",
    r"fetch\(",
]

for p in patterns:
    print("\nPattern:", p)
    matches = re.findall(p, html)
    print(matches[:20])

with open("cdsl_page.html", encoding="utf-8") as f:
    html = f.read()

for line in html.splitlines():
    if "Publications" in line or "Communique" in line:
        print(line)