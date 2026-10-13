"""Print the CPLEX outcome recorded in each run's executed main.ipynb."""
import json, re, sys
from pathlib import Path

for run in sorted(Path(__file__).parent.glob("lmlz-wide-cadence-*")):
    nbp = run / "notebooks" / "main.ipynb"
    if not nbp.exists():
        continue
    texts = []
    for c in json.load(open(nbp))["cells"]:
        for o in c.get("outputs", []):
            t = o.get("text") if o["output_type"] == "stream" else o.get("data", {}).get("text/plain")
            if t:
                texts.append("".join(t) if isinstance(t, list) else t)
    log = "".join(texts)
    if "Total (root+branch&cut)" not in log and "Presolve" not in log:
        print(f"{run.name:28s} (no solver output yet)"); continue
    m = re.search(r"CPXPARAM_TimeLimit\s+(\S+)", log)
    rows = [l for l in log.splitlines() if re.search(r"\d+\.\d+%\s*$", l) and "Gap" not in l]
    last = rows[-1].strip() if rows else "?"
    tot = re.search(r"Elapsed time = ([\d.]+) sec", log) or re.search(r"Total \(root\+branch&cut\) =\s+([\d.]+) sec", log)
    tl = "TIME LIMIT HIT" if re.search(r"[Tt]ime limit exceeded", log) else ""
    print(f"{run.name:28s} limit={m.group(1) if m else '?'}s solve={tot.group(1) if tot else '?'}s {tl}\n    last line: {last}")
