#!/usr/bin/env python3
"""Generate deterministic dependency graphs for controlled task instances."""
from __future__ import annotations
import argparse,json,random

def generate(depth,branching,delay,seed):
 rng=random.Random(seed);nodes=[];edges=[]
 levels=[]
 for d in range(depth):
  width=1 if d==0 else branching
  level=[f'n{d}_{i}' for i in range(width)];levels.append(level);nodes+=level
  if d:
   for i,v in enumerate(level): edges.append([levels[d-1][i%len(levels[d-1])],v])
 if delay>0 and depth>delay:
  for d in range(delay,depth):
   edges.append([levels[d-delay][0],levels[d][-1]])
 return {'nodes':nodes,'edges':sorted({tuple(x) for x in edges}),'depth':depth,'branching':branching,'delayed_dependency':delay,'seed':seed}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--depth',type=int,required=True);ap.add_argument('--branching',type=int,required=True);ap.add_argument('--delay',type=int,default=0);ap.add_argument('--seed',type=int,required=True);ap.add_argument('--out',required=True);a=ap.parse_args();g=generate(a.depth,a.branching,a.delay,a.seed);g['edges']=[list(x) for x in g['edges']];open(a.out,'w').write(json.dumps(g,indent=2)+'\n')
if __name__=='__main__':main()
