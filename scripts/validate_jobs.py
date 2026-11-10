#!/usr/bin/env python3
import json, sys
from pathlib import Path
from urllib.parse import urlparse
p = Path("data/jobs.json")
data = json.loads(p.read_text(encoding="utf-8"))
errors = []
seen = set()
for i, job in enumerate(data.get("jobs", [])):
    if job.get("id") in seen: errors.append(f"jobs[{i}]: duplicate id")
    seen.add(job.get("id"))
    u = urlparse(job.get("officialUrl", ""))
    if job.get("status") != "approved": errors.append(f"jobs[{i}]: status must be approved")
    if u.scheme != "https" or not u.netloc: errors.append(f"jobs[{i}]: officialUrl must be HTTPS")
    for field in ("title", "organization", "category", "lastDate"):
        if not str(job.get(field, "")).strip(): errors.append(f"jobs[{i}]: missing {field}")
if errors:
    print("\n".join(errors)); sys.exit(1)
print("jobs.json validation passed")
