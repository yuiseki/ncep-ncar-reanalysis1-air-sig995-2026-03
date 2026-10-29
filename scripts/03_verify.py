#!/usr/bin/env python3
"""Check the downloaded files with a second reader and against the manifest and the provider.

    uv run python scripts/03_verify.py     # writes docs/verify_local.json, exits 1 on any difference

Routes: netCDF4 (libnetcdf) against h5netcdf (HDF5 only) on the full arrays, and ncdump -h for the
dimensions. Also: size and sha256 against the manifest, size against a new HEAD of the provider, the
6-hourly time axis without a gap across the whole record, and the missing and out-of-range value counts.
"""

import json
import re
import subprocess
import urllib.request
from pathlib import Path

import h5netcdf
import ncepr
import netCDF4
import numpy as np

ROOT = Path(__file__).parents[1]


def head_size(url: str) -> tuple[int, str | None]:
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": ncepr.UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return int(r.headers["Content-Length"]), r.headers.get("Last-Modified")


def ncdump_dims(path: Path) -> dict[str, int]:
    out = subprocess.run(
        ["ncdump", "-h", str(path)], capture_output=True, text=True, check=True
    ).stdout
    return {k: int(v) for k, v in re.findall(r"^\s+(\w+) = (\d+)\s*;", out, re.M)} | {
        k: int(v)
        for k, v in re.findall(r"^\s+(\w+) = UNLIMITED ; // \((\d+) currently\)", out, re.M)
    }


def main() -> int:
    run = sorted((ROOT / "data" / "raw").glob("*/MANIFEST.json"))[-1].parent
    manifest = json.loads((run / "MANIFEST.json").read_text())
    problems, per_file, prev_last = [], {}, None
    total_steps = total_missing = total_out = 0
    for name, m in manifest["files"].items():
        p = run / name
        if p.stat().st_size != m["size"] or ncepr.sha256(p) != m["sha256"]:
            problems.append(f"{name}: size or sha256 differs from the manifest")
        size, lm = head_size(m["url"])
        if size != m["size"] or lm != m["last_modified_header"]:
            problems.append(
                f"{name}: the provider now says {size} bytes, {lm} (frozen: {m['size']}, {m['last_modified_header']})"
            )
        with netCDF4.Dataset(p) as a, h5netcdf.File(p, "r") as b:
            ta, tb = a["time"][:], b["time"][:]
            xa = a["air"]
            xa.set_auto_maskandscale(False)
            ra = xa[:]
            rb = b["air"][:]
            if not (np.array_equal(ta, tb) and np.array_equal(ra, rb)):
                problems.append(f"{name}: netCDF4 and h5netcdf read different arrays")
            if ra.shape != (len(ta), 73, 144):
                problems.append(f"{name}: shape {ra.shape}")
            miss = float(a["air"].getncattr("missing_value"))
            lo, hi = (float(x) for x in a["air"].getncattr("valid_range"))
            n_miss = int(np.isclose(ra, miss, rtol=0, atol=1e25).sum())
            body = ra[~np.isclose(ra, miss, rtol=0, atol=1e25)]
            n_out = int(((body < lo) | (body > hi)).sum())
            dims = ncdump_dims(p)
            if dims.get("time") != len(ta) or dims.get("lat") != 73 or dims.get("lon") != 144:
                problems.append(f"{name}: ncdump dimensions {dims}")
            hours = [float(x) for x in ta]
            tp = ncepr.time_problems(hours, 6.0)
            if tp:
                problems.append(f"{name}: time steps not 6 h at {tp[:3]}")
            if prev_last is not None and hours[0] - prev_last != 6.0:
                problems.append(f"{name}: gap to the previous file ({hours[0] - prev_last} h)")
            prev_last = hours[-1]
            first_year = ncepr.hours_to_datetime(hours[0]).year
            if (
                first_year != ncepr.year_of(name)
                or ncepr.hours_to_datetime(hours[-1]).year != first_year
            ):
                problems.append(f"{name}: the times are not all in {ncepr.year_of(name)}")
            per_file[name] = {"steps": len(ta), "missing": n_miss, "out_of_valid_range": n_out}
            total_steps += len(ta)
            total_missing += n_miss
            total_out += n_out
    res = {
        "files": len(manifest["files"]), "time_steps": total_steps, "missing_values": total_missing,
        "values_outside_valid_range": total_out, "problems": problems, "per_file": per_file,
    }  # fmt: skip
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "docs" / "verify_local.json").write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps({k: v for k, v in res.items() if k != "per_file"}, indent=1))
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
