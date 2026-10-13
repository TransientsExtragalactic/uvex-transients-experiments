# generation/

Scripts used to build, check and compare the five schedules. They were written to run from inside a
`uvex-scheduler` checkout (commit `76da5cc`), in its `runs/` directory, because they read the scheduler's
notebooks and tables. Copy them to `<uvex-scheduler>/runs/` to use them.

| Script | Purpose |
|---|---|
| `run_sweep.py` | Builds one directory per cadence under `runs/`, patches `min_cadence` in a copy of `survey.py`, sets a 1 h solver time limit, and executes the `main`, `report` and `animate` notebooks. `python runs/run_sweep.py 2d 6h 1d 4d 10d`. `SWEEP_STAGES=report,animate` runs only later stages. |
| `report_chunked.py` | Memory-lean replacement for selected cells of `report.ipynb`, which would otherwise need about 30 GB. Each replaced cell is asserted to match the original. |
| `verify_plan.py` | Independent check of a plan's constraints. |
| `solve_summary.py` | Summarises the CPLEX outcome from the executed `main.ipynb`. |
| `compute_cadence_histograms.py` | Per-pixel revisit-gap histograms for every schedule (saved as `cadence_histograms.npz`). |
| `plot_comparisons.py` | Side-by-side schedule comparison figures, written to `visualization/figures/` in this repository (copy them there). |

Setup: `uv sync --frozen` in the scheduler checkout (Python 3.14), and `docplex config --upgrade
~/Applications/CPLEX_Studio222` to use the full CPLEX engine; the pip `cplex` package is the community
edition and is capped at 1000 variables, far below this problem (about 607k binaries).
