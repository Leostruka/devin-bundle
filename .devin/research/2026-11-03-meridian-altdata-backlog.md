# Research backlog: MERIDIAN alternative-data signals (2026-11-03)

Target repo: `leostruka/MERIDIAN` (external; not present locally).
Origin: `.devin/research/2026-11-03-instagram-reels-survey.md` section 4
("Alternative data (satellite alpha), MERIDIAN-scope"); routed via contract C6
in `.devin/plans/2026-11-03-reels-adoption-plan.md`.
Status: transfer-ready backlog. No code, no repo changes, no vendored data.

## 1. Context

The source reel described three hedge-fund alt-data plays: parking-lot car
counts, floating-roof oil-tank shadow volumetrics, and weather-foresight
desks. Verified kernel: this is a real industry (RS Metrics, Orbital Insight,
Kayrros, Planet), and the academic anchor is Katona, Painter, Patatoukas and
Zeng, "On the Capital Market Consequences of Big Data: Evidence from Outer
Space": RS Metrics parking-lot feed covering 67,078 stores / 44 US retailers /
4.7M daily observations (2011-2017), with ~4-5% abnormal returns in the 3-day
window around earnings [S2][S3]. Free-tier data paths exist for most themes;
true per-car detection requires paid sub-meter imagery (see M-02).

## 2. Backlog overview

| ID  | Item                                   | Value                          | Effort | Data cost              | Depends on |
|-----|----------------------------------------|--------------------------------|--------|------------------------|------------|
| M-01| Alt-data source registry               | foundation for all items       | M      | free                   | -          |
| M-02| Car-count / lot-occupancy CV baseline  | retailer revenue nowcast       | L      | free proxy / paid true | M-01       |
| M-03| Tank-shadow + SAR volumetrics          | crude inventory nowcast        | L      | free                   | M-01       |
| M-04| Weather-foresight commodity signals    | softs/ags futures edge         | M      | free                   | M-01       |
| M-05| Signal-to-backtest harness             | makes M-02..M-04 tradable      | L      | free                   | M-01..M-04 |

## 3. M-01: alt-data source registry

Goal: a single machine-readable registry (yaml/json) describing every
upstream source, before any ingestion code. Suggested fields: `source_id`,
`provider`, `instrument`, `bands_or_fields`, `resolution`, `revisit`,
`coverage`, `access_api`, `auth`, `cost_tier`, `license`, `commercial_ok`,
`latency`, `history_start`, `signal_candidates`.

Seed entries (all verified 2026-11-03):

| source_id | Provider            | Content                          | Resolution        | Revisit/cadence      | Access                                   | Cost  | License note                          |
|-----------|---------------------|----------------------------------|-------------------|----------------------|------------------------------------------|-------|---------------------------------------|
| sent2     | ESA Copernicus      | optical MSI, 13 bands            | 10/20/60 m        | 5 d (2-sat, equator) | CDSE OData/STAC, Sentinel Hub API [S4][S5] | free | Copernicus open, attribution          |
| sent1     | ESA Copernicus      | C-band SAR, all-weather day/night| IW 5x20 m (GRD)   | 6 d nominal (2-sat)  | same CDSE APIs [S6]                       | free  | Copernicus open                        |
| planet    | Planet Labs         | PlanetScope, 4-8 bands           | ~3 m resampled    | near-daily since 2017| Planet API; Sentinel Hub resale [S7]      | paid  | commercial subscription                |
| opensky   | OpenSky Network     | ADS-B state vectors, live+hist   | n/a               | real-time            | REST API + Python/Java bindings [S8]      | free  | research/non-commercial; rate-limited  |
| aishub    | AISHub              | AIS vessel positions             | n/a               | ~1 min poll          | HTTP API (json/xml/csv) [S9]              | free* | requires feeding own receiver; paid vendors exist (MarineTraffic, Spire) |
| gfs       | NOAA/NCEP           | global forecast GRIB2            | 0.25-1.0 deg      | 4 cycles/day         | NOMADS https + grib-filter [S10]          | free  | US gov public data                     |
| ifs_od    | ECMWF               | IFS/AIFS open forecast GRIB2     | 0.25/0.1 deg      | 4 cycles/day         | data.ecmwf.int + ecmwf-opendata pkg [S11] | free  | ECMWF open-data license (CC-BY-4.0)    |
| era5      | ECMWF/Copernicus C3S| reanalysis climatology           | ~31 km, hourly    | archive              | cdsapi via ECMWF Data Store [S12]         | free  | Copernicus license                     |

Notes:
- Sentinel-1 constellation gap: S-1B lost (anomaly Dec 2021, end declared
  Aug 2022); coverage restored by S-1C (launched Dec 2024) and S-1D
  (Nov 2025); S-1C/1D also carry AIS receivers (synergy with M-01.aishub) [S6].
- Sentinel-2 archive starts 2015; PlanetScope near-daily archive starts 2017;
  these bound backtest depth for M-02/M-03.
- Registry is the dependency of every downstream item: ship it first.

## 4. M-02: car-count / lot-occupancy CV baseline

Sketch:
1. Target universe: retailer ticker -> store list -> AOI polygons
   (lot masks from OSM `amenity=parking` polygons or a segmentation pass).
2. Tile pipeline: catalog query (STAC) -> scene download -> cloud mask ->
   chip to native res -> crop by lot mask.
3. Detector: YOLO-class single-shot detector, or count-regression head
   (ResCeption-style count-in-one-look, the COWC baseline). Pretrain/fine-tune
   on COWC (32,716 annotated cars, 15 cm/pixel overhead, six regions) [S13].
4. Per-store daily count -> normalize: lot-capacity fraction, day-of-week,
   holiday calendar, cloud/gap flags -> YoY same-store delta -> factor.

Critical resolution reality-check: a passenger car is ~4.5 x 1.8 m, i.e.
sub-pixel at Sentinel-2 10 m and ~1-2 px at PlanetScope 3 m. Published
car-count work (RS Metrics; COWC) used 0.3-0.5 m imagery. Free-tier path is
therefore a lot-occupancy proxy (spectral/texture change, fill-fraction
estimate), not per-car detection; true counts need paid tasking
(SkySat ~0.5 m, Airbus Pleiades ~0.5 m, Maxar ~0.3 m) [S3][S13].

Cadence vs signal lag: the Katona edge concentrates pre-earnings; the lag it
beats is the quarterly report. Revisit mainly controls series smoothness:
near-daily (Planet) vs 5-day nominal minus cloud loss (Sentinel-2, effective
10-15+ day gaps in cloudy regions). A 5-day free feed is adequate for a
monthly/quarterly nowcast, weak for weekly.

- Value: retailer revenue nowcast ahead of earnings (verified ~4-5% / 3-day
  historical edge; crowded trade today - e-commerce shift degrades it).
- Effort: L. - Cost tier: free (proxy) / paid (true counts).
- Dependencies: M-01; store/AOI gazetteer; lot-mask polygons; COWC or
  equivalent labeled set for the detector; paid imagery contract for v2.

## 5. M-03: tank-shadow volumetrics

Geometry: a floating roof rides at height h(t) inside a fixed wall of height
H. Low roof -> interior wall shadow crescent of width w on the roof, with
(H - h) ~ w / tan(solar_zenith). Then volume V = pi * r^2 * h. Per-tank
registry needed: lat/lon, radius r, wall height H; solar angles derivable
from acquisition timestamp + location.

Resolution adequacy: US crude tanks run ~40-80 m diameter.
- Sentinel-2 10 m: 4-8 px across a tank; typical shadow widths sub-pixel.
  Marginal - only the largest tanks at low sun angles. Use as free scaffold.
- PlanetScope ~3 m: 13-27 px across; shadow crescent measurable [S7].
- SkySat 0.5 m: production-grade; paid.
- SAR alternative: roof depth changes the double-bounce/shadow signature;
  this is what Kayrros productionized on Sentinel-1 (free, all-weather,
  night-capable, ~500+ sites, 3 TB/day) [S14]. SAR path is the strongest
  free-tier candidate despite harder processing.

Validation anchor: Orbital Insight reported US inventory within ~8% of EIA
figures over ~300 weeks and beat industry reports by 2 trading days;
EIA weekly Cushing stats serve as ground truth for calibration [S15].

- Value: crude inventory nowcast ahead of EIA/IEA releases.
- Effort: L. - Cost tier: free (Sentinel-1/2), paid optional (SkySat-class).
- Dependencies: M-01; tank geo registry; solar-geometry util; SAR processing
  toolchain (GRD/SLC) for the all-weather path.

## 6. M-04: weather-foresight commodity signals

Design: crop-region masks (sul de Minas arabica, Florida citrus belt, US and
Black Sea wheat) -> extract per-cycle forecast fields (2 m TMIN, precip,
soil moisture SOILW, evapotranspiration) from GFS/IFS open data -> derive:
- frost-hours below threshold inside phenological windows,
- cumulative growing degree-days anomaly vs climatology,
- soil-moisture percentile vs ERA5 baseline,
- precip percentile (drought stress).
Composite -> per-commodity stress score -> mapped to futures
(arabica KC, FCOJ/OJ, wheat ZW, corn/soy analogs).

Event anchor: 2021-07-20 Minas Gerais frost, Tmin -1.2 C; arabica jumped
~13% that day to a 6.5-year high, then ~+10% more by 2021-07-26 after ~20%
the prior week (reel's "+25%" is roughly right) [S16][S17]. ICO monthly:
July-2021 arabica highest since Nov 2014 [S18].

Caveat: raw forecast access is public; the edge is systematic
region-crop-window mapping, ensemble disagreement metrics, and speed of
aggregation, not the data itself.

- Value: softs/ags futures positioning ahead of weather repricing.
- Effort: M. - Cost tier: free (GFS, ECMWF open data, ERA5).
- Dependencies: M-01 (gfs, ifs_od, era5); crop-region polygons; crop
  calendars; GRIB2 parsing (eccodes/cfgrib or wgrib2).

## 7. M-05: signal-to-backtest harness

Pipeline outline:
1. Ingestion: per-source adapter -> raw immutable store (parquet,
   partitioned by source/date) with both `observation_time` and
   `availability_time` columns - mandatory.
2. Normalization: UTC, trading-calendar alignment, gap/missing policy,
   capacity/baseline normalization (lot capacity, tank capacity, climatology).
3. Factor: z-scores, YoY deltas, cross-sectional ranks, surprise vs own
   history -> factor table keyed by (instrument, date).
4. Backtest: point-in-time snapshots only; event-driven (earnings, EIA
   release, weather-cycle issuance) or daily rebalance; transaction costs,
   position limits, capacity estimates.
5. Report: IC and IC decay, hit rate, Sharpe, turnover, drawdown, capacity.

Bias controls (non-negotiable):
- Look-ahead: every record carries `availability_time` (satellite publish
  latency ~hours-days, forecast issuance vs validity time, AIS/ADS-B ingest
  delay); only `availability_time <= decision_time` may enter a decision.
  Keep data vintages; never backfill-revised history silently.
- Survivorship: retailer panels lose stores (closures) and tickers
  (delisting/M&A) - dead series stay in the universe; tank/store registries
  are versioned, not overwritten.
- Multiple testing: log every tried spec in a decision ledger; pre-register
  factor definitions per signal before the backtest run.
- Overfitting: declared hold-out periods; walk-forward validation, never a
  single in-sample Sharpe.

- Value: converts M-02..M-04 outputs into falsifiable, auditable claims.
- Effort: L (v1 skeleton M). - Cost tier: free.
- Dependencies: at least one signal upstream; market/futures price history
  source (separate registry entry to add).

## 8. Cross-cutting risks

- Licensing wall: OpenSky is research/non-commercial and AISHub requires a
  contributed receiver; any commercial productization of signals built on
  them needs a license review or paid vendors. Copernicus data is open.
- Data depth limits backtests: Sentinel-2 since 2015, PlanetScope near-daily
  since 2017, Sentinel-1 since 2014 (with the 2022-2024 constellation gap).
- Crowding: the Katona-era parking-lot edge has plausibly decayed as the
  trade commoditized and retail shifted online; treat historical magnitudes
  as upper bounds, not expectations.
- Point-in-time discipline before any backtest number is trusted; without
  `availability_time`, results are fiction.

## 9. Sources

- [S1] `.devin/research/2026-11-03-instagram-reels-survey.md` (section 4)
- [S2] Katona, Painter, Patatoukas, Zeng, JFQA - https://doi.org/10.1017/s0022109023001448
- [S3] Same, SSRN working paper - https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3222741
- [S4] ESA Sentinel-2 facts and figures - https://www.esa.int/Applications/Observing_the_Earth/Copernicus/Sentinel-2/Facts_and_figures
- [S5] Copernicus Data Space Ecosystem APIs - https://dataspace.copernicus.eu/analyse/apis
- [S6] ESA Sentinel-1 facts and figures - https://www.esa.int/Applications/Observing_the_Earth/Copernicus/Sentinel-1/Facts_and_figures
- [S7] Planet PlanetScope documentation - https://docs.planet.com/data/imagery/planetscope/
- [S8] OpenSky Network API docs - https://openskynetwork.github.io/opensky-api/
- [S9] AISHub - https://www.aishub.net/ (API: https://www.aishub.net/api)
- [S10] NOAA NOMADS - https://nomads.ncep.noaa.gov/
- [S11] ECMWF open data - https://data.ecmwf.int/forecasts/
- [S12] ECMWF Data Store cdsapi setup - https://ecds.ecmwf.int/how-to-api
- [S13] COWC dataset (LLNL, Mundhenk et al. ECCV 2016) - https://gdo152.llnl.gov/cowc/ ; scripts https://github.com/LLNL/cowc
- [S14] Copernicus success story: Kayrros oil storage on Sentinel-1 - https://sentinels.copernicus.eu/web/success-stories/-/copernicus-sentinel-1-helps-monitor-oil-industry-activity
- [S15] Orbital Insight oil-tank method (company post) - https://medium.com/from-the-macroscope/the-science-behind-the-signal-tracking-unknown-oil-tanks-around-the-world-9fc917e25795
- [S16] Reuters, Brazil coffee-belt frost 2021-07-21 - https://www.reuters.com/world/americas/freak-brazil-frost-hits-heart-coffee-belt-damaging-crops-2021-07-21/
- [S17] Reuters, coffee prices surge 2021-07-26/27 - https://www.reuters.com/world/americas/coffee-prices-surge-unusual-cold-threatens-brazilian-production-2021-07-26/
- [S18] ICO coffee market report July 2021 (PDF) - https://www.ico.org/documents/cy2020-21/cmr-0721-e.pdf
