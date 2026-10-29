#!/usr/bin/env python3
"""Fetch the NOAA PSL files of NCEP/NCAR Reanalysis 1 air.sig995 (daily, 1948 onward) with checksums.

    uv run python scripts/01_collect.py          # resumable; writes data/raw/<run>/MANIFEST.json

Polite fetch: two connections per file, one file at a time, two seconds between files. The listing,
the PSL dataset page (usage and citation) are saved as they were on the day. The provider publishes
no checksums, so the sha256 here is ours; each file is checked against the Content-Length of its own HEAD.
"""

import json
import subprocess
import time
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

import ncepr

ROOT = Path(__file__).parents[1]


def get(url: str) -> tuple[bytes, dict]:
    req = urllib.request.Request(url, headers={"User-Agent": ncepr.UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read(), dict(r.headers)


def head(url: str) -> dict:
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": ncepr.UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return dict(r.headers)


def main() -> int:
    run = datetime.now(UTC).strftime("%Y%m%d")
    out = ROOT / "data" / "raw" / run
    out.mkdir(parents=True, exist_ok=True)
    docs = ROOT / "data" / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    listing, lhead = get(ncepr.BASE)
    (docs / "psl_surface_listing.html").write_bytes(listing)
    page, phead = get(ncepr.PAGE_URL)
    (docs / "psl_data_ncep_reanalysis.html").write_bytes(page)
    text = page.decode("utf-8", "replace")
    if "we ask that you acknowledge us" not in text:
        raise SystemExit("the PSL usage and citation text changed; read the page before going on")
    rows = ncepr.parse_listing(listing.decode("utf-8", "replace"))
    gaps = ncepr.missing_years([ncepr.year_of(r["name"]) for r in rows])
    if gaps:
        raise SystemExit(f"years missing in the listing: {gaps}")
    files = {}
    for i, r in enumerate(rows):
        url = ncepr.BASE + r["name"]
        h = head(url)
        want = int(h["Content-Length"])
        dest = out / r["name"]
        if not dest.exists() or dest.stat().st_size != want:
            subprocess.run(
                ["aria2c", "-q", "-x2", "-s2", "-c", "--user-agent", ncepr.UA, "-d", str(out), "-o", r["name"], url],
                check=True,
            )  # fmt: skip
            time.sleep(2)
        if dest.stat().st_size != want:
            raise SystemExit(f"{r['name']}: {dest.stat().st_size} bytes, the server said {want}")
        files[r["name"]] = {
            "url": url, "size": want, "sha256": ncepr.sha256(dest),
            "last_modified_header": h.get("Last-Modified"), "listing_modified": r["modified"].isoformat(sep=" "),
            "listing_size_printed": r["size_printed"],
        }  # fmt: skip
        print(f"{i + 1}/{len(rows)} {r['name']} {want:,}", flush=True)
    manifest = {
        "source": ncepr.BASE, "dataset_page": ncepr.PAGE_URL, "retrieved_utc": datetime.now(UTC).isoformat(),
        "listing_sha256": ncepr.sha256(docs / "psl_surface_listing.html"),
        "page_sha256": ncepr.sha256(docs / "psl_data_ncep_reanalysis.html"),
        "vintage_month": ncepr.vintage_month(rows), "files": files,
    }  # fmt: skip
    (out / "MANIFEST.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")
    print(
        f"done: {len(files)} files, {sum(f['size'] for f in files.values()):,} bytes, vintage {manifest['vintage_month']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
