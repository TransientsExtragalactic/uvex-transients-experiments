"""Side-by-side comparison figures for the LMLZ_WIDE cadence sweep.

Reads the finished runs under ``runs/`` and writes PDFs to
``runs/combined_visualizations/``. Run compute_cadence_histograms.py first for
the per-pixel cadence-distribution figure.

Colour: the five runs are an ordered quantity (the cadence), so they use one
ordinal blue ramp (light = short cadence, dark = long cadence). Steps 250/350/
450/550/650 of the reference palette, validated with --ordinal. The two bands
in the depth figure are categorical identity (blue / orange).
"""

import json
import re
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from astropy import units as u  # noqa: E402
from astropy.table import QTable, join  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "runs" / "combined_visualizations"
RUNS = ["6h", "1d", "2d", "4d", "10d"]
CADENCE_DAYS = {"6h": 0.25, "1d": 1, "2d": 2, "4d": 4, "10d": 10}
LABEL = {r: f"{r.replace('h', ' h').replace('d', ' d')}" for r in RUNS}
COLOR = dict(zip(RUNS, ["#86b6ef", "#5598e7", "#2a78d6", "#1c5cab", "#104281"]))
BAND_COLOR = {"NUV": "#2a78d6", "FUV": "#eb6834"}  # categorical slots 1, 2

INK, INK2, MUTED = "#0b0b0b", "#52514e", "#8a8985"
SURFACE, GRID = "#fcfcfb", "#e6e5e1"
plt.rcParams.update(
    {
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "text.color": INK,
        "axes.labelcolor": INK2,
        "xtick.color": INK2,
        "ytick.color": INK2,
        "axes.edgecolor": MUTED,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.color": GRID,
        "grid.linewidth": 0.6,
        "axes.axisbelow": True,
        "lines.linewidth": 1.5,
        "font.size": 9,
        "axes.titlesize": 10,
        "axes.titleweight": "normal",
        "legend.frameon": False,
        "pdf.fonttype": 42,
    }
)
SAVE = {"metadata": {"CreationDate": None}}


def save(fig, name):
    OUT.mkdir(exist_ok=True)
    fig.savefig(OUT / f"{name}.pdf", bbox_inches="tight", **SAVE)
    plt.close(fig)
    print("wrote", name)


# --------------------------------------------------------------------------
# Data
# --------------------------------------------------------------------------
def load_blocks():
    fields = QTable.read(REPO / "tables/fields.ecsv")
    blocks = QTable.read(REPO / "tables/skyblocks.ecsv")
    info = (
        join(fields, blocks)["block_id", "survey"]
        .group_by("block_id")
        .groups.aggregate(lambda x: x[0])
    )
    return dict(zip(info["block_id"].tolist(), info["survey"].tolist()))


def wide_visits(run, survey):
    """Return {block_id: sorted visit times [days since start]} for LMLZ-wide."""
    plan = QTable.read(REPO / f"runs/lmlz-wide-cadence-{run}/tables/plan.ecsv")
    t0 = plan["start_time"][0]
    is_obs = plan["action"] == "observe"
    timeblock = np.cumsum(plan["action"] == "downlink")[is_obs] - 1
    obs = plan[is_obs]
    t = (obs["start_time"] - t0).to_value(u.day)
    first = {}
    for b, k, tt in zip(obs["block_id"].tolist(), timeblock.tolist(), t.tolist()):
        if survey[b] == "lmlz_wide":
            first.setdefault(b, {}).setdefault(k, tt)  # one visit per time block
    visits = {b: np.array([d[k] for k in sorted(d)]) for b, d in first.items()}
    wide_exposure_times = np.array(
        [tt for b, tt in zip(obs["block_id"].tolist(), t.tolist()) if survey[b] == "lmlz_wide"]
    )
    return visits, wide_exposure_times


def requirement_values(run):
    """Parse the three requirement tables out of the executed report notebook."""
    nb = json.load(open(REPO / f"runs/lmlz-wide-cadence-{run}/notebooks/report.ipynb"))
    out, names = {}, ["wide", "deep", "mc"]
    k = 0
    for o in nb["cells"][27]["outputs"]:
        h = o.get("data", {}).get("text/html")
        if h:
            rows = re.findall(
                r"<tr><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td></tr>", "".join(h)
            )
            out[names[k]] = {
                "area": float(rows[0][2]),
                "NUV": float(rows[1][2]),
                "FUV": float(rows[2][2]),
            }
            k += 1
    return out


def end_label(ax, x, y, text, color, dx=4, dy=0):
    ax.annotate(
        text, (x, y), xytext=(dx, dy), textcoords="offset points",
        color=INK2, fontsize=8, va="center", annotation_clip=False,
    )


# --------------------------------------------------------------------------
# Figure 1: per-pixel cadence distribution (the report's figure, overlaid)
# --------------------------------------------------------------------------
def fig_cadence_distribution():
    path = OUT / "cadence_histograms.npz"
    if not path.exists():
        print("skip cadence distribution: run compute_cadence_histograms.py first")
        return
    d = np.load(path)
    edges = d["bin_edges"]
    XMIN = 0.1  # days; shorter gaps are off-scale (see note on the figure)
    short = edges[1:] <= XMIN + 1e-9
    short_range = {}
    fig, axs = plt.subplots(2, 1, figsize=(7.2, 7.4), sharex=True,
                            gridspec_kw={"hspace": 0.12})
    for ax, key, norm, title in (
        (axs[0], "all", d["npix"], "Whole sky"),
        (axs[1], "wide", d["npix_wide"], "LMLZ-wide footprint only"),
    ):
        peak = 0
        for run in RUNS:
            h = d[f"{key}_{run}"] / norm
            ax.stairs(h, edges, color=COLOR[run], label=LABEL[run])
            peak = max(peak, h[~short].max())
        ax.set_xscale("log")
        ax.set_xlim(XMIN, edges[-1])
        ax.set_ylim(0, 1.08 * peak)
        ax.set_title(title, loc="left", color=INK)
        ax.set_ylabel("Revisit gaps per pixel\n(per 0.1 dex bin)")
        n_short = [d[f"{key}_{run}"][short].sum() / norm for run in RUNS]
        short_range[key] = (min(n_short), max(n_short))
    # Mark where each cadence constraint bites (wide panel).
    for run in RUNS[1:]:
        axs[1].axvline(CADENCE_DAYS[run], color=COLOR[run], lw=0.8, ls=(0, (2, 3)))
    axs[1].set_xlabel("Time between successive visits to the same pixel (days)")
    axs[0].legend(title="LMLZ-wide min cadence", loc="upper right", ncols=2,
                  title_fontsize=8, fontsize=8)
    axs[1].text(0.99, 0.80,
                "dotted lines mark the\n1 d, 2 d, 4 d, 10 d minimum cadences",
                transform=axs[1].transAxes, ha="right", va="top", color=MUTED, fontsize=8)
    fig.suptitle("Cadence distribution by LMLZ-wide minimum cadence",
                 x=0.07, ha="left", fontsize=11)
    (a_lo, a_hi), (w_lo, w_hi) = short_range["all"], short_range["wide"]
    fig.text(0.07, 0.035,
             f"Gaps < {XMIN:g} d (back-to-back exposures of overlapping fields) are off-scale and nearly "
             f"identical in every run:\n{a_lo:.1f}\u2013{a_hi:.1f} per pixel over the whole sky, "
             f"{w_lo:.1f}\u2013{w_hi:.1f} per pixel in the LMLZ-wide footprint.",
             ha="left", va="top", color=MUTED, fontsize=7.5)
    save(fig, "cadence-distribution-comparison")


# --------------------------------------------------------------------------
# Figure 2: wide block revisit gaps and time to 10th visit (ECDFs)
# --------------------------------------------------------------------------
def fig_revisit_ecdf(wide):
    fig, axs = plt.subplots(1, 2, figsize=(10, 4.2), gridspec_kw={"wspace": 0.22})
    for run in RUNS:
        visits = wide[run][0]
        gaps = np.sort(np.concatenate([np.diff(v) for v in visits.values() if len(v) > 1]))
        y = np.arange(1, len(gaps) + 1) / len(gaps)
        axs[0].plot(gaps, y, color=COLOR[run], label=LABEL[run])
        tenth = np.sort([v[9] for v in visits.values() if len(v) >= 10])
        axs[1].plot(tenth, np.arange(1, len(tenth) + 1) / len(tenth), color=COLOR[run])
    axs[0].set_xscale("log")
    axs[0].set_xlabel("Gap between successive visits to a wide sky block (days)")
    axs[0].set_ylabel("Cumulative fraction of revisits")
    axs[0].set_title("Revisit gaps", loc="left")
    axs[0].legend(title="Min cadence", loc="lower right", fontsize=8, title_fontsize=8)
    axs[1].set_xlabel("Mission day on which a block gets its 10th visit")
    axs[1].set_ylabel("Cumulative fraction of wide blocks")
    axs[1].set_title("Time to minimum-visit goal", loc="left")
    axs[1].set_xlim(0, 730)
    axs[1].axvline(730, color=MUTED, lw=0.8, ls=(0, (2, 3)))
    axs[1].text(726, 0.04, "end of 2-year mission", rotation=90, ha="right",
                va="bottom", color=MUTED, fontsize=8)
    save(fig, "wide-revisit-and-completion")


# --------------------------------------------------------------------------
# Figure 3: wide exposures vs mission time
# --------------------------------------------------------------------------
def fig_wide_timeline(wide):
    fig, axs = plt.subplots(len(RUNS), 1, figsize=(8.5, 6.8), sharex=True, sharey=True,
                            gridspec_kw={"hspace": 0.12})
    bins = np.arange(0, 731, 14)
    for ax, run in zip(axs, RUNS):
        counts, _ = np.histogram(wide[run][1], bins=bins)
        ax.stairs(counts, bins, fill=True, color=COLOR[run], alpha=0.85, lw=0)
        ax.text(1.01, 0.5, f"{LABEL[run]}", transform=ax.transAxes,
                color=INK2, fontsize=8, va="center", ha="left")
        ax.set_ylim(0, None)
        ax.spines["bottom"].set_visible(False)
        ax.tick_params(axis="x", length=0)
    axs[-1].spines["bottom"].set_visible(True)
    axs[-1].tick_params(axis="x", length=3)
    axs[-1].set_xlim(0, 730)
    axs[-1].set_xlabel("Mission day")
    fig.supylabel("LMLZ-wide exposures per 14 days", color=INK2, fontsize=9)
    fig.suptitle("When the LMLZ-wide survey is observed, by minimum cadence",
                 x=0.09, y=0.95, ha="left", fontsize=11)
    save(fig, "wide-exposures-timeline")


# --------------------------------------------------------------------------
# Figure 4: depth vs cadence
# --------------------------------------------------------------------------
def fig_depth(req):
    fig, axs = plt.subplots(1, 3, figsize=(10.5, 3.9), gridspec_kw={"wspace": 0.28})
    x = np.arange(len(RUNS))
    panels = [
        ("wide", "LMLZ-wide\n(cadence varied)", "deepest 7,500 deg²"),
        ("deep", "LMLZ-deep\n(no cadence setting)", "deepest 500 deg²"),
        ("mc", "Magellanic Clouds\n(fixed 14 d cadence)", "deepest 50 deg²"),
    ]
    for ax, (key, title, sub) in zip(axs, panels):
        for band in ("NUV", "FUV"):
            y = [req[r][key][band] for r in RUNS]
            ax.plot(x, y, color=BAND_COLOR[band], marker="o", ms=5, mec=SURFACE, mew=1.2)
            end_label(ax, x[-1], y[-1], band, BAND_COLOR[band], dx=6)
        ax.set_xticks(x, [LABEL[r] for r in RUNS])
        ax.set_title(title, loc="left", color=INK)
        ax.set_xlabel("LMLZ-wide min cadence")
        ax.set_ylabel(f"Coadded limiting mag, {sub}", fontsize=8)
        # Same 0.9 mag window in every panel so slopes are directly comparable.
        mid = (min(req[r][key]["FUV"] for r in RUNS) + max(req[r][key]["NUV"] for r in RUNS)) / 2
        ax.set_ylim(mid - 0.45, mid + 0.45)
        ax.set_xlim(-0.3, len(RUNS) - 0.4)
    fig.suptitle("Coadded depth vs LMLZ-wide minimum cadence "
                 "(every requirement met by >1.5 mag; one realization each)",
                 x=0.07, y=1.06, ha="left", fontsize=10.5)
    save(fig, "depth-vs-cadence")


# --------------------------------------------------------------------------
# Figure 5: time usage
# --------------------------------------------------------------------------
def fig_time_usage():
    ACTIONS = [  # (key, label, colour): categorical slots 1-3; idle time is neutral gray
        ("observe", "Observing", "#2a78d6"),
        ("slew", "Slewing", "#eb6834"),
        ("downlink", "Downlinks", "#1baf7a"),
        ("slack", "Slack (idle)", "#8a8985"),
    ]
    total = {}
    for run in RUNS:
        plan = QTable.read(REPO / f"runs/lmlz-wide-cadence-{run}/tables/plan.ecsv")
        total[run] = {k: v.to_value(u.day) for k, v in plan.meta["total_time"].items()}

    fig, axs = plt.subplots(1, 2, figsize=(10.5, 3.8),
                            gridspec_kw={"width_ratios": [1.5, 1], "wspace": 0.28})
    ax = axs[0]
    y = np.arange(len(RUNS))[::-1]
    left = np.zeros(len(RUNS))
    for key, label, color in ACTIONS:
        w = np.array([total[r][key] for r in RUNS])
        ax.barh(y, w, left=left, height=0.62, color=color, label=label,
                edgecolor=SURFACE, linewidth=1.5)
        if key != "slack":  # slack is too thin to label in place; it is in the right panel
            for yi, li, wi in zip(y, left, w):
                if wi > 50:
                    ax.text(li + wi / 2, yi, f"{wi:.0f} d", ha="center", va="center",
                            color="white" if key == "observe" else INK, fontsize=7.5)
        left += w
    ax.set_yticks(y, [LABEL[r] for r in RUNS])
    ax.set_ylabel("LMLZ-wide min cadence")
    ax.set_xlabel("Days (of a 730-day mission)")
    ax.set_xlim(0, 735)
    ax.grid(axis="y", visible=False)
    ax.set_title("Time budget", loc="left", color=INK)
    ax.legend(ncols=4, loc="upper center", bbox_to_anchor=(0.5, -0.2), fontsize=8,
              handlelength=1, columnspacing=1.2)

    ax = axs[1]
    x = np.arange(len(RUNS))
    for key, label, color in (("slew", "Slewing", "#eb6834"), ("slack", "Slack (idle)", "#8a8985")):
        base = total["2d"][key]
        dy = [total[r][key] - base for r in RUNS]
        ax.plot(x, dy, color=color, marker="o", ms=5, mec=SURFACE, mew=1.2)
        end_label(ax, x[-1], dy[-1], label, color, dx=7)
    ax.axhline(0, color=MUTED, lw=0.8)
    ax.set_xticks(x, [LABEL[r] for r in RUNS])
    ax.set_xlim(-0.3, len(RUNS) - 0.2)
    ax.set_xlabel("LMLZ-wide min cadence")
    ax.set_ylabel("Change vs 2 d run (days)")
    ax.set_title("Only slew and slack move", loc="left", color=INK)
    ax.text(0.02, 0.98, "Observing (557.1 d) and downlinks (60.9 d)\nare identical in every run",
            transform=ax.transAxes, color=MUTED, fontsize=7.5, va="top")
    fig.suptitle("Time usage by LMLZ-wide minimum cadence", x=0.07, y=1.02,
                 ha="left", fontsize=11)
    save(fig, "time-usage-comparison")


def main():
    survey = load_blocks()
    wide = {r: wide_visits(r, survey) for r in RUNS}
    req = {r: requirement_values(r) for r in RUNS}
    fig_cadence_distribution()
    fig_revisit_ecdf(wide)
    fig_wide_timeline(wide)
    fig_depth(req)
    fig_time_usage()


if __name__ == "__main__":
    main()
