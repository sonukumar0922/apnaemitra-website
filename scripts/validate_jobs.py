
#!/usr/bin/env python3

import json
import re
import sys
from pathlib import Path
from datetime import date, datetime
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

JOBS_FILE = Path("data/jobs.json")
TODAY = datetime.now(
    ZoneInfo("Asia/Kolkata")
).date()

REQUIRED_FIELDS = (
    "id",
    "title",
    "organization",
    "category",
    "lastDate",
    "officialUrl",
    "source",
)


def normalize_text(value):
    value = str(value).strip().lower()
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def get_source_host(source):
    source = str(source).strip()

    if "://" not in source:
        source = "//" + source

    parsed = urlparse(source)

    if parsed.path not in ("", "/") or parsed.query or parsed.fragment:
        return ""

    return (parsed.hostname or "").lower().rstrip(".")


def validate_jobs():
    errors = []

    if not JOBS_FILE.exists():
        print("ERROR: data/jobs.json not found")
        return 1

    try:
        data = json.loads(
            JOBS_FILE.read_text(encoding="utf-8")
        )
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        print(f"ERROR: Invalid JSON: {exc}")
        return 1

    if not isinstance(data, dict):
        print("ERROR: JSON root must be an object")
        return 1

    jobs = data.get("jobs")

    if not isinstance(jobs, list):
        print("ERROR: jobs must be a list")
        return 1

    seen_ids = set()
    seen_fingerprints = set()

    for i, job in enumerate(jobs):
        prefix = f"jobs[{i}]"

        if not isinstance(job, dict):
            errors.append(f"{prefix}: must be an object")
            continue

        # 1. Required fields
        for field in REQUIRED_FIELDS:
            value = job.get(field)

            if not isinstance(value, str) or not value.strip():
                errors.append(f"{prefix}: missing or invalid {field}")

        if any(
            not isinstance(job.get(field), str)
            or not job.get(field, "").strip()
            for field in REQUIRED_FIELDS
        ):
            continue

        # 2. Duplicate ID
        job_id = job["id"].strip()

        if job_id in seen_ids:
            errors.append(f"{prefix}: duplicate job ID")
        seen_ids.add(job_id)

        # 3. Duplicate recruitment detection
        fingerprint = (
            normalize_text(job["organization"]),
            normalize_text(job["title"]),
            job["lastDate"].strip(),
        )

        if fingerprint in seen_fingerprints:
            errors.append(
                f"{prefix}: duplicate recruitment detected"
            )
        seen_fingerprints.add(fingerprint)

        # 4. Approval status
        if job.get("status") != "approved":
            errors.append(f"{prefix}: status must be approved")

        # 5. Strict date validation
        try:
            last_date = date.fromisoformat(job["lastDate"])

            if last_date.isoformat() != job["lastDate"]:
                raise ValueError("Date must be YYYY-MM-DD")

            if last_date < TODAY:
                errors.append(
                    f"{prefix}: application deadline has expired"
                )

        except ValueError:
            errors.append(
                f"{prefix}: invalid lastDate; use YYYY-MM-DD"
            )

        # 6. HTTPS URL validation
        try:
            parsed = urlparse(job["officialUrl"])

            if (
                parsed.scheme != "https"
                or not parsed.hostname
                or parsed.username
                or parsed.password
            ):
                errors.append(
                    f"{prefix}: officialUrl must be a valid HTTPS URL"
                )
                continue

        except ValueError:
            errors.append(f"{prefix}: invalid officialUrl")
            continue

        # 7. Source domain and URL domain matching
        source_host = get_source_host(job["source"])
        official_host = (parsed.hostname or "").lower().rstrip(".")

        if not source_host:
            errors.append(f"{prefix}: invalid source domain")

        elif not (
            official_host == source_host
            or official_host.endswith("." + source_host)
        ):
            errors.append(
                f"{prefix}: source domain does not match officialUrl"
            )

    if errors:
        print("\nJOB VALIDATION FAILED")

        for error in errors:
            print("ERROR:", error)

        print(f"\nTotal errors: {len(errors)}")
        return 1

    print("JOB VALIDATION PASSED")
    print(f"Total approved jobs: {len(jobs)}")
    print(f"Validation date (IST): {TODAY}")

    return 0


if __name__ == "__main__":
    sys.exit(validate_jobs())
