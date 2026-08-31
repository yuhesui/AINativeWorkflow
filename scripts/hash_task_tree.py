#!/usr/bin/env python3
from pathlib import Path
import hashlib, json, sys
root=Path(sys.argv[1]).resolve()
out={}
for p in sorted(x for x in root.rglob('*') if x.is_file() and '.git' not in x.parts):
    h=hashlib.sha256(p.read_bytes()).hexdigest(); out[str(p.relative_to(root))]=h
print(json.dumps(out,indent=2))
