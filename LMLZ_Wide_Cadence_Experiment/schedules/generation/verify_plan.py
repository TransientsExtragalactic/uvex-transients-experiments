"""Independently check each run's plan.ecsv against the survey constraints."""
import sys, warnings
warnings.filterwarnings("ignore")
from pathlib import Path
import numpy as np
from astropy import units as u
from astropy.table import QTable, join

REPO = Path(__file__).resolve().parent.parent
fields = QTable.read(REPO / "tables/fields.ecsv"); blocks = QTable.read(REPO / "tables/skyblocks.ecsv")
fb = join(fields, blocks)
survey_of = {b: s for b, s in zip(*np.unique(fb["block_id"], return_index=True)) } # placeholder
info = fb["block_id", "survey", "skyblock_visits_goal"].group_by("block_id").groups.aggregate(lambda x: x[0])
survey = dict(zip(info["block_id"], info["survey"])); goal = dict(zip(info["block_id"], info["skyblock_visits_goal"]))
sys.path.insert(0, str(REPO / "notebooks"))
for run in sorted(Path(__file__).parent.glob("lmlz-wide-cadence-*")):
    p = run / "tables/plan.ecsv"
    if not p.exists(): print(run.name, "no plan"); continue
    plan = QTable.read(p); obs = plan[plan["action"] == "observe"]
    # one visit per (block, downlink-interval): group observe rows by block, split at downlinks
    dl_idx = np.cumsum(plan["action"] == "downlink")
    o = plan[plan["action"] == "observe"]; o["tb"] = dl_idx[plan["action"] == "observe"]
    visits = {}
    for b, tb in set(zip(o["block_id"].tolist(), o["tb"].tolist())):
        visits.setdefault(b, []).append(tb)
    wide = [b for b in visits if survey[b] == "lmlz_wide"]
    n = np.array([len(visits[b]) for b in wide])
    gaps = np.concatenate([np.diff(np.sort(visits[b])) for b in wide if len(visits[b]) > 1]) * 6 * u.hour
    print(f"{run.name:26s} timeblocks_used={len(set(o['tb'].tolist()))}  wide blocks={len(wide)} "
          f"visits/block min={n.min()} max={n.max()}  min revisit gap={gaps.min().to(u.day):.2f}  "
          f"idle timeblocks={int((dl_idx.max()) - len(set(o['tb'].tolist())))}")
