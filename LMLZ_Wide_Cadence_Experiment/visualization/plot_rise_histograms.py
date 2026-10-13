"""Histograms of the 1/2/3-mag rise times (peak_mag <= 23), one line per schedule.

Top row:    observed bracket  t_rise_Nmag - t_last_nondet  (log hours)
Bottom row: time since explosion  t_rise_Nmag - t_explosion  (linear hours, 0-72 h)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import infant_sne_counts as counts  # noqa: E402
import numpy as np  # noqa: E402
from style import COLOR, INK2, LABEL, MUTED, RUNS, plt, save  # noqa: E402

MAGS = [1, 2, 3]
CUTS = counts.CUTS_HR
BRACKET_BINS = 10 ** np.arange(0, 4.45, 0.15)  # 1 h ... ~28000 h
EXPLOSION_BINS = np.arange(0, 72.01, 6)


def collect():
    data = {}
    tables = {run: counts.load(run) for run in RUNS}
    for mags in MAGS:
        counts.RISE_COL = f"t_rise_{mags}mag"
        for run, t in tables.items():
            keep = np.asarray(t["peak_mag"]) <= counts.PEAK_LIMIT
            for kind in ("bracket", "explosion"):
                hrs = counts.rise_hours(t, kind)
                ok = keep & np.isfinite(hrs)
                data[mags, run, kind] = (hrs[ok], np.asarray(t["weight"])[ok])
    return data


def main():
    data = collect()
    fig, axes = plt.subplots(2, 3, figsize=(11.5, 6.6))
    for col, mags in enumerate(MAGS):
        for row, (kind, bins) in enumerate(
            [("bracket", BRACKET_BINS), ("explosion", EXPLOSION_BINS)]
        ):
            ax = axes[row, col]
            for run in RUNS:
                hrs, w = data[mags, run, kind]
                ax.hist(hrs, bins=bins, weights=w, histtype="step",
                        color=COLOR[run], lw=1.5, label=LABEL[run])
            if kind == "bracket":
                ax.set_xscale("log")
                for c in CUTS:
                    ax.axvline(c, color=MUTED, lw=0.8, ls=":")
                ax.set_xlim(1, 3e4)
                ax.set_xlabel("t_rise − t_last_nondet (hours)")
                ax.set_title(f"{mags}-mag rise: observed bracket", loc="left")
            else:
                ax.set_xlim(0, 72)
                ax.set_xticks(np.arange(0, 73, 12))
                ax.set_xlabel("t_rise − t_explosion (hours)")
                ax.set_title(f"{mags}-mag rise: since explosion", loc="left")
            if col == 0:
                ax.set_ylabel("Expected events per bin")
            if row == 0 and col == 0:
                ax.legend(title="Min. cadence", loc="upper right", fontsize=8,
                          title_fontsize=8)
    # label the cut lines once
    ax = axes[0, 2]
    ymax = ax.get_ylim()[1]
    for c in CUTS:
        ax.text(c * 1.05, ymax * 0.97, f"{c} h", rotation=90, va="top", ha="left",
                fontsize=7, color=INK2)
    fig.suptitle(
        "Infant-SN rise times by schedule (LMLZ-wide minimum cadence), peak ≤ 23 mag",
        x=0.01, ha="left", fontsize=11)
    fig.text(0.01, -0.01,
             "Steps show expected events (Σ weight) per bin; only events with a defined "
             "rise are included. Dotted lines mark 6/12/24/48 h. Bracket bins are 0.15 dex; "
             "explosion bins are 6 h.",
             ha="left", va="top", fontsize=8, color=INK2)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    save(fig, "rise-time-histograms")


if __name__ == "__main__":
    main()
