#!/usr/bin/env python3
"""Push the card, terms, provenance, the NetCDF files, the index, the manifest and the docs in one commit.

uv run python src/publish.py             # dry run: list the files and their sizes
uv run python src/publish.py --push      # prints the commit sha and writes docs/revision.json
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT / "scripts"))
import ncepr  # noqa: E402

REPO = f"yuiseki/{ncepr.REPO}"
DOCS = {
    "docs/psl_data_ncep_reanalysis.html": DATA / "docs" / "psl_data_ncep_reanalysis.html",
    "docs/psl_surface_listing.html": DATA / "docs" / "psl_surface_listing.html",
    "docs/verify_local.json": ROOT / "docs" / "verify_local.json",
}


def collect() -> dict[str, Path]:
    card = (DATA / "README.md").read_text(encoding="utf-8")
    if "license: other" not in card or "acknowledge" not in card:
        raise SystemExit("the card does not carry the terms and the acknowledgement")
    run = sorted((DATA / "raw").glob("*/MANIFEST.json"))[-1].parent
    m = json.loads((run / "MANIFEST.json").read_text())
    ver = json.loads((ROOT / "docs" / "verify_local.json").read_text())
    if ver["problems"] or ver["files"] != len(m["files"]):
        raise SystemExit("the local verification does not cover the manifest")
    files = {"README.md": DATA / "README.md", "LICENSE": DATA / "LICENSE", "provenance.yaml": DATA / "provenance.yaml",
             "index.tsv": DATA / "index.tsv", "index.json": DATA / "index.json", "MANIFEST.json": run / "MANIFEST.json"}  # fmt: skip
    for name, meta in m["files"].items():
        p = run / name
        if p.stat().st_size != meta["size"] or ncepr.sha256(p) != meta["sha256"]:
            raise SystemExit(f"{name} is not the file in its manifest")
        files[f"nc/{name}"] = p
    files |= DOCS
    missing = [k for k, v in files.items() if not v.is_file()]
    if missing:
        raise SystemExit(f"missing: {missing}")
    return files


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=REPO)
    ap.add_argument("--push", action="store_true")
    a = ap.parse_args()
    files = collect()
    total = sum(p.stat().st_size for p in files.values())
    print(f"{a.repo}\n  {len(files)} files, {total:,} bytes")
    if not a.push:
        print("\ndry run. pass --push to upload")
        return 0
    from huggingface_hub import CommitOperationAdd, HfApi

    api = HfApi()
    api.create_repo(a.repo, repo_type="dataset", exist_ok=True, private=False)
    ops = [CommitOperationAdd(path_in_repo=k, path_or_fileobj=str(p)) for k, p in files.items()]
    info = api.create_commit(
        a.repo, ops, repo_type="dataset",
        commit_message="NCEP/NCAR Reanalysis 1 air.sig995 as published by NOAA PSL",
    )  # fmt: skip
    sums = {k: hashlib.sha256(p.read_bytes()).hexdigest() for k, p in files.items()}
    (ROOT / "docs" / "revision.json").write_text(
        json.dumps({"repo": a.repo, "revision": info.oid, "sha256": sums}, indent=1) + "\n"
    )
    print("pushed", a.repo, "revision", info.oid)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
