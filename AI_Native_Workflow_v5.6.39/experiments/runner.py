#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import argparse,datetime,hashlib,json,subprocess,sys,time,uuid

ROOT=Path(__file__).resolve().parents[1]

def file_hash(p):
 h=hashlib.sha256();
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()

def package_hash():
 files=[ROOT/'.ai-workflow/STATE.json',ROOT/'experiments/config/frozen_candidate.json',ROOT/'research/CLAIM_LEDGER.json']
 return hashlib.sha256(''.join(file_hash(p) for p in files if p.exists()).encode()).hexdigest()

def validate(record):
 required=['protocol_version','package_hash','run_id','condition','task_family','task_seed','dependency_graph','model','artifacts','grader','outcomes','costs','termination_reason','evidence_level']
 missing=[x for x in required if x not in record]
 if missing: raise ValueError('missing fields: '+', '.join(missing))
 if record['condition'] not in {'C0','C1','C2','C3','C1V','C2EXTRA'}: raise ValueError('unknown condition')
 if record['evidence_level'] not in {'smoke','pilot','confirmatory','post_hoc'}: raise ValueError('bad evidence level')

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--record',required=True,help='JSON emitted by a task/condition adapter');ap.add_argument('--out',default='experiments/runs/runs.jsonl');args=ap.parse_args()
 p=Path(args.record);rec=json.loads(p.read_text());rec.setdefault('protocol_version','candidate-1');rec.setdefault('package_hash',package_hash());rec.setdefault('run_id',uuid.uuid4().hex);rec.setdefault('recorded_at',datetime.datetime.now(datetime.timezone.utc).isoformat());validate(rec)
 out=ROOT/args.out;out.parent.mkdir(parents=True,exist_ok=True)
 with out.open('a',encoding='utf-8') as f:f.write(json.dumps(rec,ensure_ascii=False)+'\n')
 print(json.dumps({'ok':True,'run_id':rec['run_id'],'out':str(out)},indent=2))
if __name__=='__main__':main()
