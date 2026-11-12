#!/usr/bin/env python3
"""Validate approved Apna eMitra jobs before publication.

Run from the repository root:
    python scripts/validate_jobs.py

This validator checks data/jobs.json. It does not prove that a vacancy is genuine;
admins must verify the original notification manually before setting status=approved.
"""

import json
import re
import sys
import unicodedata
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

JOBS_FILE = Path("data/jobs.json")
TODAY = datetime.now(ZoneInfo("Asia/Kolkata")).date()

REQUIRED_FIELDS = (
    "id",
    "title",
    "organization",
    "category",
    "lastDate",
    "officialUrl",
    "source",
)

# Trusted recruiting-body domains. Add a domain only after checking that it is
# controlled by the recruiting body / government department. Do not add search,
# news, URL-shortener, or third-party aggregator domains here.
# Private employers should be added only after checking their official careers site.
TRUSTED_DOMAINS = {
    # Central recruitment / public institutions
    "ssc.gov.in",
    "upsc.gov.in",
    "rrbcdg.gov.in",
    "rrbapply.gov.in",
    "indianrailways.gov.in",
    "ibps.in",
    "sbi.co.in",
    "rbi.org.in",
    "nta.ac.in",
    # Rajasthan government / recruitment
    "rajasthan.gov.in",
    "rpsc.rajasthan.gov.in",
    "rssb.rajasthan.gov.in",
    "rsmssb.rajasthan.gov.in",
    "recruitment.rajasthan.gov.in",
}


def normalize_text(value):
    """Normalize Unicode text while retaining Hindi and other scripts."""
    value = unicodedata.normalize("NFKC", str(value)).casefold().strip()
    value = "".join(
        ch if unicodedata.category(ch)[0] in {"L", "N"} else " "
        for ch in value
    )
    return re.sub(r"\s+", " ", value).strip()


def parse_domain(value):
    """Accept a bare host or HTTPS URL containing only a host."""
    value = str(value).strip()
    if not value:
        return ""
    has_scheme = "://" in value
    candidate = value if has_scheme else "//" + value
    try:
        parsed = urlparse(candidate)
        if has_scheme and parsed.scheme.lower() != "https":
            return ""
        if parsed.path not in ("", "/") or parsed.query or parsed.fragment:
            return ""
        if parsed.username or parsed.password or parsed.port:
            return ""
        return (parsed.hostname or "").lower().rstrip(".")
    except ValueError:
        return ""


def is_same_or_subdomain(host, trusted_root):
    """Match DNS labels safely; evil-example.com must not match example.com."""
    return host == trusted_root or host.endswith("." + trusted_root)


def is_trusted_domain(host):
    return any(is_same_or_subdomain(host, root) for root in TRUSTED_DOMAINS)


def recruitment_fingerprint(job):
    """Ignore deadline changes; use notification number when supplied."""
    organization = normalize_text(job.get("organization", ""))
    title = normalize_text(job.get("title", ""))
    notification_number = normalize_text(
        job.get("notificationNo") or job.get("recruitmentId") or ""
    )
    if notification_number:
        return organization, title, notification_number
    return organization, title


def validate_jobs(jobs_file=JOBS_FILE, today=TODAY):
    errors = []

    if not jobs_file.exists():
        print(f"ERROR: {jobs_file} not found")
        return 1

    try:
        data = json.loads(jobs_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        print(f"ERROR: Invalid JSON: {exc}")
        return 1
    except OSError as exc:
        print(f"ERROR: Cannot read {jobs_file}: {exc}")
        return 1

    if not isinstance(data, dict):
        print("ERROR: JSON root must be an object")
        return 1

    jobs = data.get("jobs")
    if not isinstance(jobs, list):
        print("ERROR: jobs must be a list")
        return 1

    seen_ids = set()
    seen_fingerprints = {}

    for index, job in enumerate(jobs):
        prefix = f"jobs[{index}]"
        if not isinstance(job, dict):
            errors.append(f"{prefix}: must be an object")
            continue

        missing = False
        for field in REQUIRED_FIELDS:
            value = job.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{prefix}: missing or invalid {field}")
                missing = True
        if missing:
            continue

        # 1. Unique ID
        job_id = job["id"].strip()
        if job_id in seen_ids:
            errors.append(f"{prefix}: duplicate job ID {job_id!r}")
        seen_ids.add(job_id)

        # 2. Duplicate recruitment: a changed lastDate cannot bypass this check.
        fingerprint = recruitment_fingerprint(job)
        if fingerprint in seen_fingerprints:
            first_index = seen_fingerprints[fingerprint]
            errors.append(
                f"{prefix}: duplicate recruitment detected (first seen at jobs[{first_index}])"
            )
        else:
            seen_fingerprints[fingerprint] = index

        # 3. Only manually approved records can be published.
        if job.get("status") != "approved":
            errors.append(f"{prefix}: status must be approved")

        # 4. Strict YYYY-MM-DD date and expiry check (IST).
        try:
            raw_date = job["lastDate"].strip()
            last_date = date.fromisoformat(raw_date)
            if last_date.isoformat() != raw_date:
                raise ValueError("Date must be YYYY-MM-DD")
            if last_date < today:
                errors.append(f"{prefix}: application deadline has expired")
        except ValueError:
            errors.append(f"{prefix}: invalid lastDate; use YYYY-MM-DD")

        # 5. HTTPS URL validation.
        try:
            official = urlparse(job["officialUrl"].strip())
            if (
                official.scheme.lower() != "https"
                or not official.hostname
                or official.username
                or official.password
                or official.port not in (None, 443)
            ):
                errors.append(f"{prefix}: officialUrl must be a valid HTTPS URL")
                continue
            official_host = official.hostname.lower().rstrip(".")
        except ValueError:
            errors.append(f"{prefix}: invalid officialUrl")
            continue

        # 6. Both source and official URL must belong to a trusted domain,
        # and the official URL must be on the source host or its subdomain.
        source_host = parse_domain(job["source"])
        if not source_host:
            errors.append(f"{prefix}: source must be a domain such as ssc.gov.in")
        elif not is_trusted_domain(source_host):
            errors.append(f"{prefix}: source domain is not in TRUSTED_DOMAINS: {source_host}")
        elif not is_trusted_domain(official_host):
            errors.append(f"{prefix}: officialUrl domain is not in TRUSTED_DOMAINS: {official_host}")
        elif not is_same_or_subdomain(official_host, source_host):
            errors.append(f"{prefix}: source domain does not match officialUrl")

    if errors:
        print("\nJOB VALIDATION FAILED")
        for error in errors:
            print("ERROR:", error)
        print(f"\nTotal errors: {len(errors)}")
        return 1

    print("JOB VALIDATION PASSED")
    print(f"Total approved jobs: {len(jobs)}")
    print(f"Validation date (IST): {today}")
    return 0


if __name__ == "__main__":
    sys.exit(validate_jobs())
