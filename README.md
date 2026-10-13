# uvex-transients-experiments

Experiments that combine the UVEX survey scheduler with the UVEX transient simulator: each one asks a
specific question about a schedule scenario, runs the pipeline for it, and keeps the configurations,
schedules, data products and figures together so the result can be reproduced and revisited.

## The code these experiments use

| Project | What it provides |
|---|---|
| [uvex-scheduler](https://github.com/m4opt/uvex-scheduler) | Notebooks that build the UVEX observing plan (field of view, sky grid, survey footprints, sky blocks, the mixed-integer schedule solve with [m4opt](https://github.com/m4opt/m4opt), and the report and animation of the resulting plan). Its output is a `plan.ecsv` observing schedule. |
| [uvex-transients](https://github.com/TransientsExtragalactic/uvex-transients) | Spectral and light-curve models for kilonovae, TDEs, LFBOTs and supernovae, and the `uvex-transients` CLI that Monte Carlo samples those populations against a schedule to produce event catalogs, photometry and event summaries. |

Those repositories are developed independently. An experiment here does not modify either one: it stores only its own inputs and outputs.

## Layout

Every experiment is a top-level directory with the same structure:

```
<Experiment_Name>/
  README.md        the question, the design and how to reproduce it
  configs/         uvex-transients run configurations used for the experiment
  schedules/       the observing schedules (plan files) under test
  products/        data products written by the transient simulation, one subdirectory per schedule
  visualization/   analysis scripts and the figures they produce
```

Scripts are run from the experiment's root directory, and every path in a config or script is relative to
it, so an experiment is self-contained once the two codes above are installed.

## Experiments

| Experiment | Question |
|---|---|
| [LMLZ_Wide_Cadence_Experiment](LMLZ_Wide_Cadence_Experiment/) | How does the minimum revisit cadence of the LMLZ_WIDE survey component (6 h to 10 d) change the schedule, and how many infant supernovae does each schedule find? |

## Conventions

- **Commit configs.** Configs are committed here, never only edited in a working tree.
- **Commit inputs and small products; keep bulky output out of git.** Configs, schedules, scripts, figures
  and summary tables belong in the repository. Large or easily regenerated files (animations, intermediate
  catalogs) are gitignored, or attached to a release if they need to be shared.
- **One experiment, one directory.** Reusable plotting helpers live inside the experiment that needs them,
  and are only promoted to a shared location once a second experiment wants them.
