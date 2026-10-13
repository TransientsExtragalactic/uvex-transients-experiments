# LMLZ_Wide_Cadence_Experiment

**Question.** The UVEX schedule has a wide-area survey component, `LMLZ_WIDE`. Its *minimum cadence*, the
shortest allowed interval between visits to the same field, is a free parameter of the scheduler. How
does changing it affect the mission, and in particular how many **infant supernovae** (detected within 72 h
of explosion, with a tightly constrained rise) does each schedule find?

## Design

Five schedules, identical except for the `LMLZ_WIDE` `min_cadence` in `survey.py`:

| Label | `min_cadence` |
|---|---|
| `6h` | 6 hours |
| `1d` | 1 day |
| `2d` | 2 days |
| `4d` | 4 days |
| `10d` | 10 days |

For each schedule, the `uvex-transients` infant-SNe configuration (all supernova classes, 3-day selection
window, 23 AB magnitude screen, SNR 5) is run on that schedule's `plan.ecsv`, with the same seed (42), so
differences between runs come from the schedule.

Cadences are rounded up to the scheduler's 6-hour time blocks, and the constraint is a sliding window of at
most one visit per field.

## Contents

| Directory | Contents |
|---|---|
| [`configs/`](configs/) | `infant_sne_<cadence>.yaml`, one per schedule. They are the upstream `infant_sne.yaml` with the local schedule substituted and `photometry_pre_window: 30 day` added to every class. |
| [`schedules/`](schedules/) | `<cadence>/plan.ecsv` and `run.json` for each schedule, `fov/chips.ds9`, and [`generation/`](schedules/generation/) with the scripts that built and checked them. |
| [`products/`](products/) | Transient-simulation outputs (`final_catalog`, `exposure`, `photometry`, `event_summary`, all `.ecsv`) per schedule. See its README. |
| [`visualization/`](visualization/) | Scripts and figures. `figures/` holds the cross-schedule comparisons, `schedule_reports/<cadence>/` the scheduler's own report figures for each schedule. |

## Reproducing

**1. Schedules** (needs a `uvex-scheduler` checkout, Python 3.14 with `uv`, and a full CPLEX license):
see [`schedules/generation/README.md`](schedules/generation/README.md). The finished `plan.ecsv` files are
already included here, so this step is only needed to regenerate or change them.

**2. Transient simulation**, from this directory, once per cadence:

```bash
uvex-transients run configs/infant_sne_2d.yaml --out-dir products/2d/
```

The CLI reads checkpoint files that already exist in the output directory (its log shows it reading
`final_catalog.ecsv`). After changing a config, remove `final_catalog.ecsv`, `photometry.ecsv` and
`event_summary.ecsv` or pass `--overwrite`, so that old products are not reused.

**3. Figures and counts**, from this directory:

```bash
python visualization/infant_sne_counts.py 2        # counts for a 2-mag rise (1, 2 or 3)
python visualization/plot_rise_histograms.py       # 1/2/3-mag rise-time histograms
python visualization/plot_example_lightcurves.py   # example counted / not-counted light curves
```

## Provenance

| | |
|---|---|
| `uvex-scheduler` | [`76da5cc`](https://github.com/m4opt/uvex-scheduler) (`main`, "Tune histograms"); Python 3.14.8, `m4opt` 4.0.0, CPLEX Studio 22.2 (full engine) |
| Solver | MILP with a 1 h limit per schedule. All five solves reached the optimum (objective 2921, every 6-hour time block filled) |
| Report notebook | A memory-lean chunked copy of `report.ipynb` was used, because the stock notebook needs about 30 GB. Each replaced cell was validated against the original on a subset. |
| `uvex-transients` | [`32c8779`](https://github.com/TransientsExtragalactic/uvex-transients) (`dev`); the configs here are the source of truth for the run settings |
| Seed | 42 (`generate.seed`) |

## Results so far

*Preliminary: the transient products in `products/` are being regenerated with the 30-day pre-explosion
photometry window, and the transient-based figures will be added when that finishes. The counts below come
from the earlier run of the same schedules and seed, and depend only on the event summaries.*

**Schedule.** The five schedules are nearly the same mission. Observing (557.1 d) and downlink (60.9 d) time
are identical; slewing varies between 73.2 d and 74.7 d and slack between 37.6 d and 39.1 d, a trade of
about 1.5 d (under 0.2% of the 730-day mission). Figures: `visualization/figures/` (cadence distribution,
revisit and completion, wide-exposure timeline, depth versus cadence, time usage).

**Infant supernovae.** Expected events with peak magnitude ≤ 23, a rise of the stated size defined, and an
*observed bracket* (`t_rise − t_last_nondet`) under 48 h:

| `min_cadence` | 2-mag rise | 3-mag rise |
|---|---|---|
| 6 h | 115 | 23 |
| 1 d | 116 | 31 |
| 2 d | 62 | 18 |
| 4 d | 10 | 5 |
| 10 d | 14 | 4 |

Schedules with a cadence of 1 d or shorter find several times more events with a tight bracket than those
at 4 d or longer. Counts are from a single seed, so differences between neighbouring schedules at the
small end (4 d versus 10 d, 6 h versus 1 d) are within Poisson noise. Measured instead from the explosion
time, the counts barely depend on the schedule, because that measures how many events are intrinsically
fast rather than how well the explosion time is constrained.
