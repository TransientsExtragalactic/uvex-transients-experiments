"""Example light curves of bright, nearby SNe that do / do not enter the 2-mag, <48 h sample.

Schedule: 2 d minimum cadence. Photometry covers observations after explosion only, so a last
non-detection before explosion is marked by its time but not drawn.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import infant_sne_counts as counts  # noqa: E402
import numpy as np  # noqa: E402
from astropy.table import QTable  # noqa: E402
from style import BAND_COLOR, INK, INK2, MUTED, PRODUCTS, plt, save  # noqa: E402

RUN = "2d"
MAGS = 2
CUT_HR = 48
COUNTED = [108058, 48938, 137112, 111037]
NOT_COUNTED = [97355, 40551, 7654, 24560]
XMAX = 30.0
NAMES = {"ia_sne": "Ia", "iip_excess_sne": "IIP-excess", "iib_sne": "IIb", "ic_sne": "Ic",
         "ib_sne": "Ib", "icbl_sne": "Ic-BL", "slsne": "SLSN"}
SNR = 5.0
WINDOW_D = 3.0  # infant_sne.yaml duration_limit: only observations within 3 d of explosion count
SURFACE_ALPHA = (0.99, 0.99, 0.98, 0.85)


def mask_none(x):
    return None if bool(np.all(getattr(x, "mask", False))) else x


def verdict(row, hrs):
    t_nd, t_rise = mask_none(row["t_last_nondet"]), mask_none(row[f"t_rise_{MAGS}mag"])
    if t_nd is None:
        return "no earlier non-detection", False
    if t_rise is None:
        return f"no {MAGS}-mag rise within {WINDOW_D:.0f} d", False
    delay = (t_nd - row["t_explosion"]).to("d").value
    when = f"{abs(delay):.0f} d {'before' if delay < 0 else 'after'}"
    if hrs < CUT_HR:
        return f"bracket {hrs:.1f} h", True
    return f"bracket {hrs:,.0f} h (non-det. {when})", False


def panel(ax, row, phot, hrs):
    t0 = row["t_explosion"]
    reason, counted = verdict(row, hrs)
    t_nd, t_rise = mask_none(row["t_last_nondet"]), mask_none(row[f"t_rise_{MAGS}mag"])
    lo = (t_nd - t0).to("d").value if t_nd is not None else None
    hi = (t_rise - t0).to("d").value if t_rise is not None else None

    det_mags = []
    for band, color in BAND_COLOR.items():
        q = phot[phot["band"] == band]
        t = q["rel_time"].to("d").value
        det = np.asarray(q["snr"]) >= SNR
        mag = np.asarray(q["ab_mag"])
        lim = -2.5 * np.log10(SNR * q["flux_err"].to("Jy").value / 3631)
        order = np.argsort(t)
        ax.plot(t[order][det[order]], mag[order][det[order]], color=color, lw=0.8, zorder=2)
        ax.errorbar(t[det], mag[det], yerr=np.asarray(q["mag_err"])[det], fmt="o", ms=4,
                    color=color, ecolor=color, elinewidth=0.8, label=band, zorder=3)
        ax.plot(t[~det], lim[~det], "v", ms=5, mfc="none", mec=color, mew=1.0, zorder=3)
        det_mags += list(mag[det & (t <= XMAX)])

    if lo is not None and hi is not None and lo > -1:
        ax.axvspan(max(lo, -1), hi, color=MUTED, alpha=0.25, lw=0, zorder=1)
    elif lo is not None and lo > -1:
        ax.axvline(lo, color=MUTED, lw=1, ls="--", zorder=1)
    if hi is not None:
        ax.axvline(hi, color=INK2, lw=0.8, ls=":", zorder=1)

    ax.axvline(WINDOW_D, color=MUTED, lw=0.8, ls="--", zorder=1)
    ax.set_xlim(-1, XMAX)
    top, bottom = min(det_mags) - 0.6, min(max(det_mags) + 1.2, 24.5)
    ax.set_ylim(bottom, top)
    ax.set_xlabel("Days since explosion")
    ctype, z, pk = NAMES[str(row["transient_type"])], row["redshift"], row["peak_mag"]
    ax.set_title(f"{ctype}  z = {z:.3f}  peak {pk:.1f} mag", loc="left", fontsize=9.5, pad=18)
    mark = "✓" if counted else "✗"
    ax.text(0.0, 1.015, f"{mark} {reason}", transform=ax.transAxes, va="bottom", ha="left",
            fontsize=8.5, color=INK2)
    if lo is not None and lo <= -1:
        ax.annotate(f"last non-detection at {lo:,.0f} d", xy=(0.3, 0.05),
                    xycoords="axes fraction", fontsize=7.5, color=INK2)


def main():
    R = PRODUCTS / RUN
    summary = QTable.read(R / "event_summary.ecsv")
    phot = QTable.read(R / "photometry.ecsv")
    counts.RISE_COL = f"t_rise_{MAGS}mag"
    hrs_all = counts.rise_hours(summary, "bracket")

    fig, axes = plt.subplots(2, 4, figsize=(13, 6.6))
    for r, (ids, label) in enumerate([(COUNTED, "COUNTED"), (NOT_COUNTED, "NOT COUNTED")]):
        for c, eid in enumerate(ids):
            i = int(np.flatnonzero(np.asarray(summary["event_id"]) == eid)[0])
            ax = axes[r, c]
            panel(ax, summary[i], phot[phot["event_id"] == eid], hrs_all[i])
            if c == 0:
                ax.set_ylabel("AB magnitude")
        fig.text(0.005, 0.74 - r * 0.46, label, rotation=90, va="center", fontsize=10,
                 color=INK)
    axes[0, 0].legend(loc="lower left", fontsize=8)
    fig.suptitle(
        f"Bright, nearby SNe: counted / not counted in the {MAGS}-mag, < {CUT_HR} h sample "
        f"({RUN} schedule)", x=0.02, ha="left", fontsize=11)
    fig.text(0.02, -0.005,
             "Circles: detections (SNR ≥ 5, 1σ errors). Triangles: 5σ limits. Grey band: observed "
             f"bracket from last non-detection to the first detection ≥ {MAGS} mag above that "
             "limit (dotted line = that detection).\nDashed line: end of the 3 d infant-SN window; "
             "only observations before it enter the selection.",
             fontsize=8, color=INK2, va="top")
    fig.tight_layout(rect=(0.02, 0, 1, 0.95))
    save(fig, "example-lightcurves-2mag")
    return fig


if __name__ == "__main__":
    main()
