#!/usr/bin/env python3
"""Discover recruitment-related news links. These are leads, never verified vacancies."""
import hashlib, json, os, re, urllib.parse, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from email.utils import parsedate_to_datetime

ROOT = Path(__file__).resolve().parents[1]
sources = json.loads((ROOT / "sources.json").read_text(encoding="utf-8"))
pending_path = ROOT / "data" / "pending-jobs.json"
pending = json.loads(pending_path.read_text(encoding="utf-8"))
existing = {x.get("id") for x in pending.get("jobs", [])}
headers = {"User-Agent": "Apna-eMitra-JobDiscovery/1.0 (contact: support@apnaemitra.in)"}

def google_news_rss(query):
    params = urllib.parse.urlencode({"q": query, "hl": "en-IN", "gl": "IN", "ceid": "IN:en"})
    return "https://news.google.com/rss/search?" + params

def clean_text(s):
    return re.sub(r"\s+", " ", s or "").strip()

added = []
for item in sources["queries"]:
    url = google_news_rss(item["query"])
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            xml_data = response.read()
        root = ET.fromstring(xml_data)
        for node in root.findall("./channel/item")[:15]:
            title = clean_text(node.findtext("title"))
            link = clean_text(node.findtext("link"))
            pub = clean_text(node.findtext("pubDate"))
            if not title or not link:
                continue
            # Keep a stable ID based on category + title + link.
            job_id = hashlib.sha256((item["category"] + "|" + title + "|" + link).encode()).hexdigest()[:16]
            if job_id in existing:
                continue
            try:
                published = parsedate_to_datetime(pub).astimezone(timezone.utc).isoformat()
            except Exception:
                published = ""
            added.append({
                "id": job_id,
                "title": title,
                "organization": "To be confirmed",
                "category": item["category"],
                "qualification": "Official notification देखें",
                "location": "As per official notification",
                "vacancies": "Not confirmed",
                "ageLimit": "Not confirmed",
                "lastDate": "",
                "fee": "Official notification देखें",
                "salary": "Official notification देखें",
                "discoveryUrl": link,
                "officialUrl": "",
                "source": "Google News discovery lead",
                "discoveredAt": datetime.now(timezone.utc).isoformat(),
                "publishedAt": published,
                "status": "pending",
                "adminNote": "Verify the original official notification. Fill organization, officialUrl, eligibility, dates and fee before setting status=approved."
            })
            existing.add(job_id)
    except Exception as exc:
        print(f"Feed failed for {item['category']}: {exc}")

if added:
    pending["jobs"].extend(added)
    pending["lastDiscovery"] = datetime.now(timezone.utc).isoformat()
    pending_path.write_text(json.dumps(pending, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"New discovery leads: {len(added)}")
