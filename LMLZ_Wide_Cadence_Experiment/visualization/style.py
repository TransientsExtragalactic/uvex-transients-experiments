"""Shared plot style and paths for the LMLZ_WIDE cadence experiment.

The five schedules are an ordered quantity (the minimum cadence), so they use one ordinal
blue ramp: light = short cadence, dark = long cadence. The two UVEX bands are categorical
identity (blue / orange).
"""

import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
# Transient-simulation outputs: <PRODUCTS>/<cadence>/{event_summary,photometry,...}.ecsv
PRODUCTS = Path(os.environ.get("UVEX_PRODUCTS", ROOT / "products"))
FIGURES = ROOT / "visualization" / "figures"

RUNS = ["6h", "1d", "2d", "4d", "10d"]
LABEL = {r: r.replace("h", " h").replace("d", " d") for r in RUNS}
COLOR = dict(zip(RUNS, ["#86b6ef", "#5598e7", "#2a78d6", "#1c5cab", "#104281"]))
BAND_COLOR = {"NUV": "#2a78d6", "FUV": "#eb6834"}

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


def save(fig, name):
    FIGURES.mkdir(exist_ok=True)
    fig.savefig(
        FIGURES / f"{name}.pdf", bbox_inches="tight", metadata={"CreationDate": None}
    )
    plt.close(fig)
    print("wrote", FIGURES / f"{name}.pdf")
