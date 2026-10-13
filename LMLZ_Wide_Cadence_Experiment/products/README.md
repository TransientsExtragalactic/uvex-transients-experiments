# products/

Output of `uvex-transients run configs/infant_sne_<cadence>.yaml --out-dir products/<cadence>/`, one
subdirectory per schedule:

| File | Contents |
|---|---|
| `final_catalog.ecsv` | Events that pass the magnitude and SNR cuts |
| `exposure.ecsv` | Expected events and effective exposure per transient type and time bin |
| `photometry.ecsv` | Synthetic photometry of the selected events, including the 30 days before explosion |
| `event_summary.ecsv` | One row per event: detections, last non-detection, `t_rise_{1,2,3}mag`, peak magnitude, expected-event `weight` |

*These are being regenerated with the 30-day pre-explosion photometry window; they will be added when the
run finishes.*
