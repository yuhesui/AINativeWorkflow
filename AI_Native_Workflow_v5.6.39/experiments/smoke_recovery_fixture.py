#!/usr/bin/env python3
"""Deterministic structural smoke test for dependency-local invalidation.
Not an agent-performance experiment.
"""
from collections import defaultdict, deque
import json
from pathlib import Path

def impact_cone(edges, readers):
    out=defaultdict(list)
    for a,b in edges: out[a].append(b)
    q=deque(readers); seen=set(readers)
    while q:
        u=q.popleft()
        for v in out[u]:
            if v not in seen: seen.add(v); q.append(v)
    return sorted(seen)

def main():
    nodes=['collect','normalize','theory','experiment','table','paper','release']
    edges=[('collect','normalize'),('normalize','experiment'),('theory','paper'),('experiment','table'),('table','paper'),('paper','release')]
    read_sets={'collect':{'source'},'normalize':{'raw'},'theory':{'sources'},'experiment':{'normalized'},'table':{'results'},'paper':{'theory','table'},'release':{'paper'}}
    changed={'normalized'}
    direct=[n for n in nodes if read_sets[n]&changed]
    cone=impact_cone(edges,direct)
    result={'kind':'deterministic_structural_smoke','changed_keys':sorted(changed),'direct_readers':direct,'impact_cone':cone,'full_rerun_nodes':len(nodes),'local_repair_nodes':len(cone),'saved_nodes':len(nodes)-len(cone),'claim_boundary':'This checks implementation of declared dependency locality only; it is not comparative language-agent evidence.'}
    p=Path(__file__).resolve().parent/'smoke_recovery_fixture.json';p.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__': main()
