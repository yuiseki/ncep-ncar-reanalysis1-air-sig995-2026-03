"""Constants and helpers shared by the scripts of ncep-ncar-reanalysis1-air-sig995-2026-03."""

import hashlib
import re
from datetime import datetime, timedelta
from pathlib import Path

BASE = "https://downloads.psl.noaa.gov/Datasets/ncep.reanalysis/surface/"
PAGE_URL = "https://psl.noaa.gov/data/gridded/data.ncep.reanalysis.html"
UA = "Mozilla/5.0 (research; yuiseki)"
PREFIX = "air.sig995."
REPO = "ncep-ncar-reanalysis1-air-sig995-2026-03"
_ROW = re.compile(
    r'<a href="(' + re.escape(PREFIX) + r'\d{4}\.nc)">[^<]*</a>(?:</td>\s*<td[^>]*>)?\s*'
    r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2})\s*(?:</td>\s*<td[^>]*>)?\s*(\S+?)\s*(?:<|$)"
)


def parse_listing(html: str) -> list[dict]:
    """Rows of the Apache index for the wanted variable only: name, modified, size as printed."""
    return [
        {"name": n, "modified": datetime.strptime(m, "%Y-%m-%d %H:%M"), "size_printed": s}
        for n, m, s in _ROW.findall(html)
    ]


def year_of(name: str) -> int:
    return int(name.removeprefix(PREFIX).removesuffix(".nc"))


def vintage_month(rows: list[dict]) -> str:
    return max(r["modified"] for r in rows).strftime("%Y-%m")


def missing_years(years: list[int]) -> list[int]:
    return sorted(set(range(min(years), max(years) + 1)) - set(years))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def time_problems(hours: list[float], step: float) -> list[tuple[int, float]]:
    """(index, difference) of every place where consecutive times do not differ by exactly step."""
    return [
        (i, hours[i + 1] - hours[i])
        for i in range(len(hours) - 1)
        if hours[i + 1] - hours[i] != step
    ]


def hours_to_datetime(h: float) -> datetime:
    """The files count hours since 1800-01-01 00:00 (netCDF units string)."""
    return datetime(1800, 1, 1) + timedelta(hours=float(h))
