#!/usr/bin/env python3
"""Write a small index of the downloaded files: dimensions, time range, variable attributes, checksums.

    uv run python scripts/02_index.py     # writes data/index.tsv and data/index.json

The NetCDF files are published as they are. This index is the only added file; it is read from the files.
"""

import json
from pathlib import Path

import ncepr
import netCDF4

ROOT = Path(__file__).parents[1]
COLUMNS = [
    "file",
    "year",
    "bytes",
    "sha256",
    "time_steps",
    "first_time_utc",
    "last_time_utc",
    "lat",
    "lon",
]


def main() -> int:
    run = sorted((ROOT / "data" / "raw").glob("*/MANIFEST.json"))[-1].parent
    manifest = json.loads((run / "MANIFEST.json").read_text())
    rows, attrs = [], None
    for name, m in manifest["files"].items():
        with netCDF4.Dataset(run / name) as ds:
            t = ds["time"][:]
            air = ds["air"]
            rows.append({
                "file": name, "year": ncepr.year_of(name), "bytes": m["size"], "sha256": m["sha256"],
                "time_steps": len(t), "first_time_utc": ncepr.hours_to_datetime(t[0]).isoformat(sep=" "),
                "last_time_utc": ncepr.hours_to_datetime(t[-1]).isoformat(sep=" "),
                "lat": ds.dimensions["lat"].size, "lon": ds.dimensions["lon"].size,
            })  # fmt: skip
            if attrs is None:
                attrs = {
                    "variable": {k: str(air.getncattr(k)) for k in air.ncattrs()},
                    "global": {k: str(ds.getncattr(k)) for k in ds.ncattrs() if k != "title"},
                }
    lines = ["\t".join(COLUMNS)] + ["\t".join(str(r[c]) for c in COLUMNS) for r in rows]
    (ROOT / "data" / "index.tsv").write_text("\n".join(lines) + "\n")
    info = {"run": run.name, "files": len(rows), "variable_attributes_of_first_file": attrs}
    (ROOT / "data" / "index.json").write_text(json.dumps(info, indent=1, ensure_ascii=False) + "\n")
    print(f"{len(rows)} files, {sum(r['time_steps'] for r in rows):,} time steps")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
