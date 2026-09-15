"""Copy daily reports from the shared Drive folder into source/.

Picks up files named YYYY-MM-DD.md (plain files or Google Docs), checks the
front matter, and writes them to source/ only when new or changed.
"""
import json
import os
import pathlib
import re
import sys

import requests
import yaml
from google.auth.transport.requests import Request
from google.oauth2 import service_account

FOLDER_ID = os.environ["DRIVE_FOLDER_ID"]
SOURCE = pathlib.Path(__file__).resolve().parent.parent / "source"
NAME = re.compile(r"^(\d{4}-\d{2}-\d{2})\.md$")
API = "https://www.googleapis.com/drive/v3/files"

creds = service_account.Credentials.from_service_account_info(
    json.loads(os.environ["GDRIVE_SA_KEY"]),
    scopes=["https://www.googleapis.com/auth/drive.readonly"],
)
creds.refresh(Request())
session = requests.Session()
session.headers["Authorization"] = f"Bearer {creds.token}"


def list_files():
    params = {
        "q": f"'{FOLDER_ID}' in parents and trashed = false",
        "fields": "nextPageToken, files(id, name, mimeType)",
        "pageSize": 100,
    }
    while True:
        r = session.get(API, params=params)
        r.raise_for_status()
        body = r.json()
        yield from body["files"]
        if "nextPageToken" not in body:
            return
        params["pageToken"] = body["nextPageToken"]


def download(f):
    if f["mimeType"] == "application/vnd.google-apps.document":
        r = session.get(f"{API}/{f['id']}/export", params={"mimeType": "text/markdown"})
    else:
        r = session.get(f"{API}/{f['id']}", params={"alt": "media"})
    r.raise_for_status()
    return r.content.decode("utf-8").replace("\r\n", "\n")


TAGS = {
    # Alan
    "Hava Savunma", "C-UAS", "Topçu", "Mühimmat", "Roket ve Füze", "Barut ve Patlayıcı",
    "Deniz Sistemleri", "Dolanan Mühimmat", "Hafif Silah", "Mayın ve Geçit Açma", "KBRN",
    "Sivil Pazar",
    # Ürün
    "TOLGA", "BORAN", "ATTİLA", "URAN", "BOZKIR", "DENİZHAN", "PİRANA", "BARKIN", "MALAMAN",
    "MPT-76",
    # Coğrafya
    "Türkiye", "ABD", "AB", "NATO/NSPA", "Polonya", "Körfez", "Suudi Arabistan", "Katar",
    "Mısır", "Afrika", "Güneydoğu Asya", "Malezya", "Balkanlar", "Kafkasya ve Orta Asya",
    "Güney Asya",
    # Tema
    "İhale", "İhracat", "Ortak Üretim", "Rakip", "Regülasyon", "Tedarik Zinciri",
    "Savunma Bütçesi", "Doktrin", "Fuar",
}


def valid(text, date):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return "no front matter"
    meta = yaml.safe_load(m.group(1)) or {}
    if str(meta.get("date")) != date:
        return f"front matter date {meta.get('date')!r} does not match filename"
    if not meta.get("title"):
        return "missing title"
    if meta.get("alarm") and not meta.get("alarm_title"):
        return "alarm is true but alarm_title is empty"
    tags = meta.get("tags") or []
    if not 1 <= len(tags) <= 8:
        return f"expected 1-8 tags, got {len(tags)}"
    if unknown := [t for t in tags if str(t) not in TAGS]:
        return f"tags not in the allowed list: {unknown}"
    return None


files = list(list_files())
print(f"folder has {len(files)} file(s)")
changed, problems = [], []
for f in files:
    name = f["name"] if f["name"].endswith(".md") else f["name"] + ".md"
    m = NAME.match(name)
    if not m:
        continue
    text = download(f)
    if err := valid(text, m.group(1)):
        problems.append(f"{name}: {err}")
        continue
    dest = SOURCE / name
    if dest.exists() and dest.read_text(encoding="utf-8") == text:
        continue
    dest.write_text(text, encoding="utf-8")
    changed.append(name)

print("updated:", ", ".join(changed) or "nothing")
for p in problems:
    print("::error::" + p)
sys.exit(1 if problems else 0)
