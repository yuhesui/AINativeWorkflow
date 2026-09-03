#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import argparse,json,statistics,collections,math

def load(path):
 return [json.loads(x) for x in Path(path).read_text().splitlines() if x.strip()]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('jsonl');ap.add_argument('--out',default='experiments/results/descriptive.json');a=ap.parse_args();rows=load(a.jsonl)
 groups=collections.defaultdict(list)
 for r in rows:groups[(r['condition'],r.get('effective_horizon',r['dependency_graph'].get('depth')))].append(r)
 out={'evidence_levels':sorted({r['evidence_level'] for r in rows}),'groups':[],'claim_boundary':'Descriptive output inherits the weakest evidence level represented; it is not confirmatory unless every included run is confirmatory and the protocol is frozen.'}
 for (c,h),xs in sorted(groups.items(),key=lambda z:(z[0][0],z[0][1] or -1)):
  vals=[float(x['outcomes'].get('end_to_end_success',0)) for x in xs];prop=[float(x['outcomes'].get('failure_propagation_size',0)) for x in xs]
  out['groups'].append({'condition':c,'effective_horizon':h,'n':len(xs),'success_mean':statistics.mean(vals),'propagation_mean':statistics.mean(prop)})
 p=Path(a.out);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
