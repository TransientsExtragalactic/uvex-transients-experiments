"""Per-pixel revisit-gap histograms for every cadence run.

Same quantity as the report's "Cadence distribution" figure (gap between
successive visits to the same HEALPix pixel, nside=2048, same footprints), but
histogrammed on one shared set of log bins so runs can be overlaid, and split
into all-sky and LMLZ-wide-footprint pixels.

Memory-lean: footprints are generated in chunks and discarded; only each pixel's
last visit time is kept.
"""

import os
import sys
import warnings
from functools import partial
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "runs" / "combined_visualizations"
RUNS = ["6h", "1d", "2d", "4d", "10d"]
CHUNK = 2000
# Shared log10(days) bin edges: 0.01 d ... ~1260 d, 0.1 dex wide.
BIN_EDGES = 10 ** np.arange(-2.0, 3.15, 0.1)


def main():
    os.chdir(REPO / "notebooks")  # survey.py uses ../survey-footprints paths
    sys.path.insert(0, str(REPO / "notebooks"))

    from astropy.coordinates import ICRS
    from astropy.table import QTable
    from astropy_healpix import HEALPix
    from ligo.skymap.util import progress_map_vectorized
    from m4opt.fov import footprint_healpix
    from regions import Regions
    from survey import mission

    hpx = HEALPix(nside=2048, frame=ICRS())
    wide_pixels = footprint_healpix(
        hpx, Regions.read(REPO / "survey-footprints/lmlz-wide.ds9")
    )
    wide_mask = np.zeros(hpx.npix, dtype=bool)
    wide_mask[wide_pixels] = True
    print(f"LMLZ-wide footprint: {wide_mask.sum()} pixels", flush=True)

    result = {"bin_edges": BIN_EDGES, "npix": hpx.npix, "npix_wide": wide_mask.sum()}
    for run in RUNS:
        plan = QTable.read(REPO / f"runs/lmlz-wide-cadence-{run}/tables/plan.ecsv")
        obs = plan[plan["action"] == "observe"]
        mjd = obs["start_time"].mjd
        assert np.all(np.diff(mjd) > 0), "observations must be in time order"

        last_visit = np.full(hpx.npix, np.nan)
        hist_all = np.zeros(len(BIN_EDGES) - 1)
        hist_wide = np.zeros(len(BIN_EDGES) - 1)
        for start in range(0, len(obs), CHUNK):
            sel = slice(start, start + CHUNK)
            footprints = progress_map_vectorized(
                partial(footprint_healpix, hpx, mission.fov),
                obs["target_coord"][sel].unmasked,
                obs["roll"][sel].unmasked,
                jobs=None,
                ascii=True,
            )
            for t_obs, footprint in zip(mjd[sel], footprints):
                previous = last_visit[footprint]
                seen = ~np.isnan(previous)
                gaps = t_obs - previous[seen]
                hist_all += np.histogram(gaps, bins=BIN_EDGES)[0]
                hist_wide += np.histogram(
                    gaps[wide_mask[footprint[seen]]], bins=BIN_EDGES
                )[0]
                last_visit[footprint] = t_obs
        result[f"all_{run}"] = hist_all
        result[f"wide_{run}"] = hist_wide
        print(f"{run}: done ({len(obs)} observations)", flush=True)

    OUT.mkdir(exist_ok=True)
    np.savez(OUT / "cadence_histograms.npz", **result)
    print("saved", OUT / "cadence_histograms.npz", flush=True)


if __name__ == "__main__":
    main()
