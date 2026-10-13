"""Infant-SN counts per schedule: peak-magnitude mask, then 3-mag rise-time bins.

Rise time definitions (both reported):
  bracket : t_rise_3mag - t_last_nondet  (what an observer measures; upper limit on the true rise)
  explosion: t_rise_3mag - t_explosion   (true time since explosion, simulation truth)
"""
import warnings
warnings.filterwarnings("ignore")
import sys
from pathlib import Path
import numpy as np
from astropy.table import QTable

sys.path.insert(0, str(Path(__file__).resolve().parent))
from style import PRODUCTS, RUNS  # noqa: E402

CUTS_HR = [6, 12, 24, 48]
PEAK_LIMIT = 23.0
MAGS = sys.argv[1] if len(sys.argv) > 1 else "3"  # rise magnitude: 1, 2 or 3
RISE_COL = f"t_rise_{MAGS}mag"


def load(run):
    return QTable.read(PRODUCTS / run / "event_summary.ecsv")


def rise_hours(t, kind):
    ref = t["t_last_nondet"] if kind == "bracket" else t["t_explosion"]
    dt = (t[RISE_COL] - ref).to("hr").value
    return np.ma.filled(np.ma.asarray(dt, dtype=float), np.nan)  # NaN where undefined


def tabulate(t, kind):
    peak_ok = np.asarray(t["peak_mag"]) <= PEAK_LIMIT
    hrs = rise_hours(t, kind)
    w = np.asarray(t["weight"])
    types = sorted(set(map(str, t["transient_type"]))) 
    ty = np.asarray(t["transient_type"]).astype(str)
    rows = {}
    for name in types + ["ALL"]:
        sel = peak_ok & ((ty == name) if name != "ALL" else True)
        r = {"total": int(np.sum(ty == name)) if name != "ALL" else len(t),
             "peak<=23": int(sel.sum()), "peak_w": float(w[sel].sum()),
             "defined": int((sel & np.isfinite(hrs)).sum())}
        for c in CUTS_HR:
            m = sel & np.isfinite(hrs) & (hrs < c)
            r[c] = (int(m.sum()), float(w[m].sum()))
        rows[name] = r
    return rows


if __name__ == "__main__":
    for kind in ("bracket", "explosion"):
        print(f"\n######## {MAGS}-mag rise, definition: {kind}")
        for run in RUNS:
            t = load(run)
            rows = tabulate(t, kind)
            print(f"\n== cadence {run}  (rows={len(t)})")
            print(f"{'type':16s}{'summ':>6s}{'pk<=23':>8s}{'defined':>8s}" + "".join(f"{'<'+str(c)+'h N(Σw)':>16s}" for c in CUTS_HR))
            for name, r in rows.items():
                print(f"{name:16s}{r['total']:6d}{r['peak<=23']:8d}{r['defined']:8d}" +
                      "".join(f"{r[c][0]:6d}({r[c][1]:7.1f})" for c in CUTS_HR))
