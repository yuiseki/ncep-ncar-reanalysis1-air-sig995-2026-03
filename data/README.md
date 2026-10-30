---
license: other
license_name: noaa-psl-acknowledgement
license_link: LICENSE
language:
- en
tags:
- climate
- reanalysis
- temperature
- netcdf
- ncep
- noaa
pretty_name: NCEP/NCAR Reanalysis 1, air temperature at sigma 0.995, 6-hourly, 1948 to 2026-03-17
viewer: false
---

# NCEP/NCAR Reanalysis 1: air temperature at sigma level 0.995, 4 times daily (1948 to 2026-03-17)

NOAA PSL が配布する NCEP/NCAR 再解析 1 の「シグマ 0.995 面の気温」(地表付近の気温、1 日 4 回、2.5 度格子)を、
1948 年から 2026-03-17 まで凍結したコピーです。NetCDF は配布されたままで、何も変えていません。

A frozen copy of the NetCDF files `air.sig995.YYYY.nc` of NCEP/NCAR Reanalysis 1 ("4xDaily Air temperature at
sigma level 995") as published by the NOAA Physical Sciences Laboratory, acquired on 2026-10-29.
The files are byte for byte what the provider serves. Only `index.tsv`, `index.json` and the saved provider pages
and checksums under `docs/` and `MANIFEST.json` are added.

## Source

- Provider: NOAA Physical Sciences Laboratory (PSL), dataset page <https://psl.noaa.gov/data/gridded/data.ncep.reanalysis.html>.
- Files: <https://downloads.psl.noaa.gov/Datasets/ncep.reanalysis/surface/> (one file per year; the listing and the dataset page as they were on the day are in `docs/`).
- Version: the files are served without a version number. The newest Last-Modified among the 79 files is
  2026-03-19 08:28:00 (the 2026 file, which is partial); the other files date from 2023 or earlier. This is why
  the repository name carries 2026-03.

## Contents

| path | what it is |
| --- | --- |
| `nc/air.sig995.YYYY.nc` | the 79 yearly NetCDF files, 1948 to 2026, 1.74 GB in all |
| `index.tsv`, `index.json` | per file: bytes, sha256, time steps, first and last time, grid size; the variable attributes |
| `MANIFEST.json` | per file: URL, size, sha256, the Last-Modified header and the listing time, as fetched |
| `docs/` | the provider's listing and dataset page as saved, and `verify_local.json` |
| `LICENSE`, `provenance.yaml` | the terms and acknowledgement, and the provenance |

- Variable `air(time, lat, lon)`: air temperature at 0.995 sigma, units degK, float, missing value -9.96921e+36.
- Grid: 73 latitudes (90 to -90, 2.5 degree) by 144 longitudes (0 to 357.5 east, 2.5 degree).
- Time: hours since 1800-01-01 00:00 (UTC), every 6 hours (00, 06, 12, 18 UTC). 114,264 time steps in all,
  from 1948-01-01 00:00:00 to 2026-03-17 18:00:00.
- The files are non-packed NetCDF4 (chunked, deflated), converted by the provider in 2014/09 (see the `history`
  attribute). The provider's `title` attribute differs by year, so it is not repeated here.

## Terms and acknowledgement

The files carry no licence text. PSL's dataset page says (USAGE & CITATION, quoted):

> Please note: If you acquire data products from PSL, we ask that you acknowledge us in your use of the data.
> This may be done by including text such as "data provided by the NOAA PSL, Boulder, Colorado, USA, from their website at https://psl.noaa.gov" in any documents or publications using these data. We would also
> appreciate receiving a copy of the relevant publications. This will help PSL to justify keeping the data freely
> available online in the future.

Please include that acknowledgement. The maintainer of this repository treats this condition as equivalent to
CC BY style attribution, because no licence text exists for the files themselves; this is the maintainer's reading,
not a statement by NOAA. The data are provided as published, without warranty, and this repository is not endorsed
by NOAA or PSL. The card therefore says `license: other` and not a Creative Commons licence.

The standard description of the reanalysis is Kalnay et al. (1996), Bull. Amer. Meteor. Soc. 77, 437-471
(the files' `References` attribute points to the PSL page; the paper is named here as the usual citation and
was not checked against the PSL page, whose reference list is loaded dynamically).

## Verification

`scripts/03_verify.py` re-reads every file: size and sha256 against the manifest, size and Last-Modified against a
new request to the provider, the full `air` array and the time axis with two readers (netCDF4 and h5netcdf, equal),
the dimensions with `ncdump -h`, a 6-hourly time axis without a gap across all files, and the counts of missing
and out-of-range values: 0 missing values, 0 outside the provider's valid range, 0 problems.
The provider publishes no checksums, so the sha256 values are ours.

## Reproduce

Scripts, tests and logs: <https://github.com/yuiseki/ncep-ncar-reanalysis1-air-sig995-2026-03>. `scripts/01_collect.py` fetches, `02_index.py` indexes,
`03_verify.py` checks, `04_card.py` writes this card.
