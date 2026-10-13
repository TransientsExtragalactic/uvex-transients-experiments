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
| [`products/`](products/) | Transient-simulation outputs (`final_catalog`, `exposure`, `photometry`, `event_summary`, all `.ecsv`) per schedule. |
| [`visualization/`](visualization/) | Scripts and figures. `figures/` holds the cross-schedule comparisons, `schedule_reports/<cadence>/` the scheduler's own report figures for each schedule. |

## Reproducing

**1. Schedules.** The finished `plan.ecsv` files are already included, so this step is only needed to
regenerate or change them. It needs a `uvex-scheduler` checkout (`uv sync --frozen`, Python 3.14) and the full
CPLEX engine (`docplex config --upgrade ~/Applications/CPLEX_Studio222`; the pip `cplex` package is the
community edition, capped at 1000 variables). Copy the scripts in `schedules/generation/` to
`<uvex-scheduler>/runs/` and run them from the checkout:

| Script | Purpose |
|---|---|
| `run_sweep.py` | Builds one directory per cadence, patches `min_cadence`, sets a 1 h solver limit and runs the `main`, `report` and `animate` notebooks: `python runs/run_sweep.py 2d 6h 1d 4d 10d`. `SWEEP_STAGES=report,animate` runs only later stages. |
| `report_chunked.py` | Memory-lean replacement for selected `report.ipynb` cells (the stock notebook needs about 30 GB). |
| `verify_plan.py` | Independent check of a plan's constraints. |
| `solve_summary.py` | CPLEX outcome from the executed `main.ipynb`. |
| `compute_cadence_histograms.py` | Per-pixel revisit-gap histograms, saved as `cadence_histograms.npz`. |
| `plot_comparisons.py` | Schedule comparison figures, to copy into `visualization/figures/`. |

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
