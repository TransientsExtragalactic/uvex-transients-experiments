"""Memory-lean rewrite of selected cells of notebooks/report.ipynb.

The committed report holds every (observation x HEALPix pixel) pair in memory
at once (~650 million pairs for a 53k-observation plan, ~30 GB). Only per-pixel
reductions are needed, so these replacements compute the same quantities
chunk by chunk:

* visit map           -> batched bincount
* limiting magnitudes -> running sum of 10**(0.8 (m - zp)) and running max
* cadence histogram   -> last-visit time per pixel, histogram accumulated

Nothing else (nside, bandpasses, S/N, dwell, bins, plotting) is changed. Each
replacement asserts the old cell begins as expected so a changed notebook
fails loudly instead of being silently mis-patched.
"""

import json

CELL_5_OLD = "# HEALPix map of the number of visits for each pixel.\nvisit_map = np.bincount(np.concatenate(footprints), minlength=hpx.npix)"
CELL_5_NEW = """# HEALPix map of the number of visits for each pixel.
# (Accumulated in batches to avoid concatenating every footprint at once.)
visit_map = np.zeros(hpx.npix, dtype=np.intp)
for start in range(0, len(footprints), 1000):
    visit_map += np.bincount(
        np.concatenate(footprints[start : start + 1000]), minlength=hpx.npix
    )"""

# cell index -> (expected first line of old source, new source)
REPLACEMENTS = {
    11: (
        "# The HEALPix field footprints are ragged in length.",
        """# Per-observation inputs. The (observation x pixel) arrays are built one
# chunk at a time in the next cell instead of for the whole plan at once.
observer_location = obs["observer_location"].unmasked
obstime = obs["start_time"].unmasked""",
    ),
    12: (
        "# The pixel array is too large to process all at once without running out of",
        """# Process the observations in chunks, accumulating only the per-pixel
# reductions that are needed:
#   * coadded limiting magnitude: running sum of 10 ** (0.8 * (limmag - zeropoint))
#   * deepest single-dwell limiting magnitude: running maximum
zeropoint = 24  # prevent catastrophic overflow
chunk_size = 250
bands = list(mission.detector.bandpasses)

coadd_sum_by_band = {band: np.zeros(hpx.npix) for band in bands}
deepest_limmags_by_band = {band: np.full(hpx.npix, -np.inf) for band in bands}

for start in tqdm(range(0, len(obs), chunk_size)):
    sel = slice(start, start + chunk_size)
    chunk_footprints = footprints[sel]

    # The HEALPix field footprints are ragged in length. Pad them into a
    # rectangular array so that we can broadcast over time and HEALPix index.
    shape = (max(len(footprint) for footprint in chunk_footprints), len(chunk_footprints))
    ipix = np.zeros(shape, dtype=np.intp)
    mask = np.zeros(shape, dtype=bool)
    for i, footprint in enumerate(chunk_footprints):
        ipix[: len(footprint), i] = footprint
        mask[len(footprint) :, i] = True
    target_coord = hpx.healpix_to_skycoord(ipix)

    with observing(
        observer_location=observer_location[sel],
        target_coord=target_coord,
        obstime=obstime[sel],
    ):
        for band in bands:
            limmag = mission.detector.get_limmag(
                snr=snr,
                exptime=dwell,
                source_spectrum=source_spectrum,
                bandpass=band,
            ).value
            valid_ipix = ipix[~mask]
            valid_limmag = limmag[~mask]
            coadd_sum_by_band[band] += np.bincount(
                valid_ipix,
                weights=10 ** (0.8 * (valid_limmag - zeropoint)),
                minlength=hpx.npix,
            )
            np.maximum.at(deepest_limmags_by_band[band], valid_ipix, valid_limmag)""",
    ),
    13: (
        "# Calculate stacked limiting magnitude, assuming Gaussian noise.",
        """# Calculate stacked limiting magnitude, assuming Gaussian noise.
coadded_limmags_by_band = {
    key: 1.25 * np.log10(value) + zeropoint for key, value in coadd_sum_by_band.items()
}""",
    ),
    14: (
        "deepest_limmags_by_band = {key: np.full(hpx.npix, -np.inf) for key in limmags_by_band}",
        "# (deepest_limmags_by_band was accumulated in the chunked loop above.)",
    ),
    20: (
        "t = np.repeat(obs[\"start_time\"].mjd, [len(f) for f in footprints])",
        """# Gap between successive visits to the same pixel, computed by walking the
# observations in time order and remembering each pixel's last visit time.
obs_mjd = obs["start_time"].mjd
assert np.all(np.diff(obs_mjd) > 0), "observations must be in time order"


def iter_gaps():
    last_visit = np.full(hpx.npix, np.nan)
    for t_obs, footprint in zip(obs_mjd, footprints):
        previous = last_visit[footprint]
        yield t_obs - previous[~np.isnan(previous)]
        last_visit[footprint] = t_obs


gap_min, gap_max = np.inf, -np.inf
for gaps in iter_gaps():
    if len(gaps):
        gap_min = min(gap_min, gaps.min())
        gap_max = max(gap_max, gaps.max())""",
    ),
    21: (
        "fig, ax = plt.subplots()\nbins = decibel_bin_edges(gap.min(), gap.max())",
        """fig, ax = plt.subplots()
bins = decibel_bin_edges(gap_min, gap_max)
counts = np.zeros(len(bins) - 1)
for gaps in iter_gaps():
    counts += np.histogram(gaps, bins=bins)[0]
# Draw the accumulated histogram with the same bars as ax.hist(gap, bins=bins, ...).
ax.hist(bins[:-1], bins=bins, weights=counts / hpx.npix)
sky_fraction_area_axes(ax)
ax.set_xscale("log")
ax.set_xlabel("Time delay (days)")
ax.set_title("Cadence distribution")
ax.grid()
fig.savefig(
    "../visualizations/cadence-distribution.pdf", metadata={"CreationDate": None}
)""",
    ),
}


def _lines(text: str) -> list[str]:
    return text.splitlines(keepends=True)


def patch_report(text: str) -> str:
    nb = json.loads(text)
    cells = nb["cells"]

    src5 = "".join(cells[5]["source"])
    assert src5.count(CELL_5_OLD) == 1, "report cell 5 changed"
    cells[5]["source"] = _lines(src5.replace(CELL_5_OLD, CELL_5_NEW))

    for index, (old_start, new) in REPLACEMENTS.items():
        old = "".join(cells[index]["source"])
        assert cells[index]["cell_type"] == "code" and old.startswith(old_start), (
            f"report cell {index} changed"
        )
        cells[index]["source"] = _lines(new)
    return json.dumps(nb, indent=1) + "\n"
