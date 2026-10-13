# schedules/

`<cadence>/plan.ecsv` is the observing plan for each `LMLZ_WIDE` minimum cadence (`6h`, `1d`, `2d`, `4d`,
`10d`), and `<cadence>/run.json` records the setting and solver limit used. `fov/chips.ds9` is the
field-of-view definition that `uvex-transients` pairs with a plan (the `fov_path` in the configs).

The plans are about 17 MB each. [`generation/`](generation/) holds the scripts that produced and checked them.
