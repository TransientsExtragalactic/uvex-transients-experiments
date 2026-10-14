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
window, 23 AB magnitude screen, SNR 5) is run on that schedule's plan, with the same seed (42), so
differences between runs come from the schedule.

Cadences are rounded up to the scheduler's 6-hour time blocks, and the constraint is a sliding window of at
most one visit per field.

## Contents

| Directory | Contents |
|---|---|
| [`configs/`](configs/) | `infant_sne_<cadence>.yaml`, one per schedule. They are the upstream `infant_sne.yaml` with the local schedule substituted and `photometry_pre_window: 30 day` added to every class. |
| [`schedules/`](schedules/) | `plan_lmlz_wide_<cadence>.ecsv`, the observing plan for each schedule. |
| [`products/`](products/) | Transient-simulation outputs (`final_catalog`, `exposure`, `photometry`, `event_summary`, all `.ecsv`) per schedule. |
| [`notebooks/`](notebooks/) | `bracket_distribution.ipynb`: cumulative count of events with an observed rise bracket shorter than T, per schedule. `rapid_rise_rate.ipynb`: events whose photometry shows a rise faster than a given rate (mag per day) from the last non-detection. Settings are in each notebook's first section. |
| [`visualization/`](visualization/) | Per-schedule cadence distributions (`plan_lmlz_wide_<cadence>_cadence-distribution.pdf`), the time-usage comparison and the wide revisit and completion comparison. |

## Reproducing

**1. Transient simulation**, from any directory:

```bash
code/run_infant_sne.sh            # all five cadences
code/run_infant_sne.sh 2d 6h      # or a chosen subset
```

Each run starts from an empty working directory, so no old checkpoint is reused, and its outputs land in
`products/` as `infant_sne_<cadence>_{final_catalog,exposure,photometry,event_summary}.ecsv`. The script uses
`uvex-transients` from `PATH` (override with `UVEX_TRANSIENTS=/path/to/uvex-transients`). The configs point
at `products/chips.ds9`, the field-of-view definition used with the schedules.
