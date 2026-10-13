"""Sweep the LMLZ_WIDE minimum cadence.

For each cadence, build a self-contained run directory under ``runs/`` holding
patched copies of the notebooks, then execute main -> report -> animate.

Only two things differ from the committed code, and only in the copies:

* ``survey.py``: the ``lmlz_wide`` ``min_cadence`` value
* ``main.ipynb``: ``Model(verbose=True)`` -> ``Model(verbose=True, timelimit=...)``

The fov/, survey-footprints/ and the upstream tables (fields.ecsv,
skyblocks.ecsv) are shared with the repo through symlinks.
"""

import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from report_chunked import patch_report  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
RUNS = REPO / "runs"
JUPYTER = REPO / ".venv" / "bin" / "jupyter"

# label -> survey.py expression
CADENCES = {
    "6h": "6 * u.hour",
    "1d": "1 * u.day",
    "2d": "2 * u.day",
    "4d": "4 * u.day",
    "10d": "10 * u.day",
}
SOLVER_TIMELIMIT = "1 * u.hour"
NOTEBOOKS = ["main", "report", "animate"]
import os
STAGES = os.environ.get("SWEEP_STAGES", ",".join(NOTEBOOKS)).split(",")


def patch_survey(text: str, expr: str) -> str:
    pattern = re.compile(
        r'(name="lmlz_wide",.*?min_cadence=)[^,\n]+(,)', flags=re.DOTALL
    )
    new, n = pattern.subn(rf"\g<1>{expr}\g<2>", text, count=1)
    assert n == 1, "could not patch lmlz_wide min_cadence"
    return new


def patch_main(text: str) -> str:
    old = "with Model(verbose=True) as m:"
    assert text.count(old) == 1, "expected exactly one Model(verbose=True) call"
    return text.replace(old, f"with Model(verbose=True, timelimit={SOLVER_TIMELIMIT}) as m:")


def write_notebooks(run: Path, stages: list[str]):
    for nb in stages:
        src = (REPO / "notebooks" / f"{nb}.ipynb").read_text()
        if nb == "main":
            src = patch_main(src)
        elif nb == "report":
            src = patch_report(src)
        (run / "notebooks" / f"{nb}.ipynb").write_text(src)


def build_run(label: str, expr: str) -> Path:
    run = RUNS / f"lmlz-wide-cadence-{label}"
    if "main" not in STAGES:
        # Downstream stages only: keep the existing plan, refresh the notebooks.
        assert (run / "tables" / "plan.ecsv").exists(), f"{run.name}: no plan.ecsv yet"
        write_notebooks(run, stages=STAGES)
        return run
    if run.exists():
        shutil.rmtree(run)
    (run / "notebooks").mkdir(parents=True)
    (run / "tables").mkdir()
    (run / "visualizations").mkdir()

    # Shared, read-only inputs
    for name in ("fov", "survey-footprints"):
        (run / name).symlink_to(REPO / name)
    for name in ("fields.ecsv", "skyblocks.ecsv"):
        (run / "tables" / name).symlink_to(REPO / "tables" / name)

    # Patched survey configuration
    survey = (REPO / "notebooks" / "survey.py").read_text()
    (run / "notebooks" / "survey.py").write_text(patch_survey(survey, expr))

    write_notebooks(run, stages=NOTEBOOKS)

    (run / "run.json").write_text(
        json.dumps(
            {
                "label": f"LMLZ_WIDE min_cadence = {label}",
                "lmlz_wide_min_cadence": expr,
                "solver_timelimit": SOLVER_TIMELIMIT,
                "report_notebook": "memory-lean chunked copy (see runs/report_chunked.py)",
                "shared_inputs": ["fov/", "survey-footprints/", "tables/fields.ecsv", "tables/skyblocks.ecsv"],
            },
            indent=2,
        )
        + "\n"
    )
    return run


def execute(run: Path, nb: str) -> float:
    t0 = time.time()
    log = run / f"{nb}.log"
    with log.open("w") as f:
        subprocess.run(
            [str(JUPYTER), "execute", f"{nb}.ipynb", "--timeout=-1", "--inplace"],
            cwd=run / "notebooks",
            stdout=f,
            stderr=subprocess.STDOUT,
            check=True,
        )
    return time.time() - t0


def main(labels: list[str]):
    for label in labels:
        run = build_run(label, CADENCES[label])
        print(f"=== {run.name}", flush=True)
        for nb in STAGES:
            try:
                dt = execute(run, nb)
            except subprocess.CalledProcessError:
                print(f"  {nb}: FAILED (see {run.name}/{nb}.log)", flush=True)
                break
            print(f"  {nb}: ok in {dt / 60:.1f} min", flush=True)


if __name__ == "__main__":
    main(sys.argv[1:] or list(CADENCES))
