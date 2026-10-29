#!/usr/bin/env python3
"""Read the repository back from the Hub at the recorded revision and compare it with the local copy.

    uv run python scripts/05_verify_hub.py     # needs docs/revision.json from src/publish.py --push

Checks the file list and sizes at the revision, the sha256 of every file, and reads each NetCDF again
(time steps, shape) against index.tsv.
"""

import hashlib
import json
from pathlib import Path

import netCDF4
from huggingface_hub import HfApi, hf_hub_download

ROOT = Path(__file__).parents[1]


def main() -> int:
    rev = json.loads((ROOT / "docs" / "revision.json").read_text())
    repo, sha = rev["repo"], rev["revision"]
    api = HfApi()
    info = api.dataset_info(repo, revision=sha, files_metadata=True)
    hub_files = {s.rfilename: s.size for s in info.siblings if s.rfilename != ".gitattributes"}
    out, bad = {"repo": repo, "revision": sha, "files_on_hub": len(hub_files)}, []
    if set(hub_files) != set(rev["sha256"]):
        bad.append(f"file list differs: {set(hub_files) ^ set(rev['sha256'])}")
    cache = ROOT / "data" / "hub_readback"
    for name, want in rev["sha256"].items():
        p = Path(hf_hub_download(repo, name, repo_type="dataset", revision=sha, local_dir=cache))
        if (
            hashlib.sha256(p.read_bytes()).hexdigest() != want
            or hub_files.get(name) != p.stat().st_size
        ):
            bad.append(f"checksum or size {name}")
    idx = [ln.split("\t") for ln in (cache / "index.tsv").read_text().splitlines()[1:]]
    steps = 0
    for r in idx:
        with netCDF4.Dataset(cache / "nc" / r[0]) as ds:
            if len(ds["time"]) != int(r[4]) or ds["air"].shape != (int(r[4]), int(r[7]), int(r[8])):
                bad.append(f"{r[0]}: time steps or shape differ from index.tsv")
            steps += len(ds["time"])
    out |= {
        "files_checked": len(rev["sha256"]),
        "netcdf_files": len(idx),
        "time_steps": steps,
        "problems": bad,
    }
    (ROOT / "docs" / "verify_hub.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))
    if bad:
        return 1
    print(f"OK: the repository at {sha} equals the local copy")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
