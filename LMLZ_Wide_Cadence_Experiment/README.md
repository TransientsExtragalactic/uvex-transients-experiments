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
| [`visualization/`](visualization/) | Scripts and figures. `figures/` holds the cross-schedule comparisons, `schedule_reports/<cadence>/` the scheduler's own report figures for each schedule. |

## Reproducing

**1. Transient simulation**, from this directory, once per cadence. The configs expect the uvex-scheduler
repository's `fov/` directory (it provides `fov/chips.ds9`) in this directory, e.g. as a symlink:

```bash
uvex-transients run configs/infant_sne_2d.yaml --out-dir products/2d/
```

The CLI reads checkpoint files that already exist in the output directory (its log shows it reading
`final_catalog.ecsv`). After changing a config, remove `final_catalog.ecsv`, `photometry.ecsv` and
`event_summary.ecsv` or pass `--overwrite`, so that old products are not reused.

**2. Figures and counts**, from this directory:

```bash
python visualization/infant_sne_counts.py 2        # counts for a 2-mag rise (1, 2 or 3)
python visualization/plot_rise_histograms.py       # 1/2/3-mag rise-time histograms
python visualization/plot_example_lightcurves.py   # example counted / not-counted light curves
```
