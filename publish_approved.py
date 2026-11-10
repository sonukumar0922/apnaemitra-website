#!/usr/bin/env python3
"""Publish only records explicitly marked approved and carrying an HTTPS official URL."""
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
pending_path = ROOT / "data/pending-jobs.json"
public_path = ROOT / "data/jobs.json"

pending = json.loads(pending_path.read_text(encoding="utf-8"))
public = json.loads(public_path.read_text(encoding="utf-8"))
public_jobs = public.setdefault("jobs", [])
known = {j.get("id") for j in public_jobs}
remaining, published = [], []

for job in pending.get("jobs", []):
    official = urlparse(job.get("officialUrl", ""))
    required = ["id", "title", "organization", "category", "officialUrl", "lastDate"]
    complete = all(str(job.get(k, "")).strip() for k in required)
    if job.get("status") == "approved" and complete and official.scheme == "https" and official.netloc and job.get("id") not in known:
        job["verificationDate"] = datetime.now(timezone.utc).date().isoformat()
        public_jobs.append(job)
        published.append(job)
        known.add(job.get("id"))
    else:
        remaining.append(job)

if published:
    public["lastUpdated"] = datetime.now(timezone.utc).isoformat()
    public_path.write_text(json.dumps(public, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
pending["jobs"] = remaining
pending_path.write_text(json.dumps(pending, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Published approved jobs: {len(published)}")
