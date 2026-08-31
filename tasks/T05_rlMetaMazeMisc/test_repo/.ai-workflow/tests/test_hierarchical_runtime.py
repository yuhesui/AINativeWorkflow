import json
import tempfile
import unittest
from pathlib import Path
import sys

HERE=Path(__file__).resolve()
sys.path.insert(0,str(HERE.parents[1]))
from aw.hierarchy import WorkflowStore, WorkflowError, canonical_role

class HierarchicalRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory(); self.root=Path(self.t.name); self.s=WorkflowStore(self.root); self.s.init(checkpoint_interval=3)
    def tearDown(self): self.t.cleanup()
    def plan(self,n=3,interval=None):
        pid=self.s.create_plan("Research plan","Produce defensible result",checkpoint_interval=interval)
        ids=[]
        for i in range(n):
            deps=[ids[-1]] if ids else []
            ids.append(self.s.add_phase(f"P{i+1}",f"Objective {i+1}",owner=("Main","Theory","Experiment")[i%3],dependencies=deps,acceptance=["evidence exists"]))
        self.s.approve_plan(); return pid,ids
    def test_one_plan_authorizes_several_phases(self):
        _,ids=self.plan(5); st=self.s.load(); p=st["plans"][st["active_plan_id"]]
        self.assertEqual(len(p["phases"]),5); self.assertEqual(p["status"],"approved")
    def test_autonomous_ordinary_phase_progression(self):
        _,ids=self.plan(3); self.s.start_phase(ids[0]); out=self.s.complete_phase(ids[0],acceptance_results={"ac-1":True})
        self.assertEqual(out["next_phase_id"],ids[1]); self.assertEqual(self.s.load()["plans"][self.s.load()["active_plan_id"]]["phases"][ids[1]]["status"],"active")
    def test_periodic_checkpoint_trigger(self):
        _,ids=self.plan(3,interval=2); self.s.start_phase(ids[0]); self.s.complete_phase(ids[0],acceptance_results={"ac-1":True})
        self.s.complete_phase(ids[1],acceptance_results={"ac-1":True}); st=self.s.load(); self.assertEqual(st["plans"][st["active_plan_id"]]["status"],"checkpoint_due"); self.assertEqual(st["checkpoints"][-1]["kind"],"periodic")
    def test_immediate_material_escalation(self):
        _,ids=self.plan(1); self.s.start_phase(ids[0]); eid=self.s.escalate("scientific_claim_change","the theorem failed",phase_id=ids[0]); st=self.s.load(); self.assertEqual(st["escalations"][-1]["id"],eid); self.assertEqual(st["plans"][st["active_plan_id"]]["status"],"escalated")
    def test_reconstructable_lineage(self):
        _,ids=self.plan(1); ph=ids[0]; dic=self.s.create_dic(ph,evidence_requirements=["tests.json"]); eps=self.s.generate_eps(ph,[{"operation":"run tests"}]); self.s.start_phase(ph); act=self.s.record_action(ph,eps_id=eps,action="run tests",result="pass",evidence_paths=["tests.json"]); line=self.s.lineage(ph)
        self.assertEqual(line["dic_id"],dic); self.assertIn(eps,line["eps_ids"]); self.assertIn(act,line["action_ids"]); self.assertIn("Prompt/Run <= EPS",line["relation"])
    def test_main_theory_experiment_ownership_and_aliases(self):
        _,ids=self.plan(3); st=self.s.load(); p=st["plans"][st["active_plan_id"]]; self.assertEqual([p["phases"][x]["owner"] for x in ids],["Main","Theory","Experiment"]); self.assertEqual(canonical_role("Orchestrator"),"Main"); self.assertEqual(canonical_role("Researcher"),"Theory")
    def test_state_recovery_from_package_alone(self):
        _,ids=self.plan(1); self.s.create_dic(ids[0]); self.s.generate_eps(ids[0],[{"operation":"inspect"}]); recovered=WorkflowStore(self.root).recover(); self.assertTrue(recovered["ok"],recovered)
    def test_legacy_compatibility_index(self):
        (self.root/'GOAL.md').write_text('# Legacy goal\n'); out=self.s.migrate_legacy(); self.assertIn('GOAL.md',out['indexed']); self.assertTrue(self.s.load()['legacy']['aliases_enabled'])
    def test_dependency_block(self):
        _,ids=self.plan(2); self.assertRaises(WorkflowError,self.s.start_phase,ids[1])
    def test_verification_outcomes(self):
        _,ids=self.plan(1); self.s.start_phase(ids[0]); self.s.verify(ids[0],"repair",rationale="local test failed"); st=self.s.load(); self.assertEqual(st["plans"][st["active_plan_id"]]["phases"][ids[0]]["verification"][-1]["outcome"],"repair")

    def test_dic_is_one_multiview_phase_package(self):
        _,ids=self.plan(1); ph=ids[0]
        self.s.create_dic(ph, architecture_text="# Architecture\nnew repo tree", test_matrix_text="# Matrix\nA x B")
        st=self.s.load(); phase=st["plans"][st["active_plan_id"]]["phases"][ph]
        d=self.root/phase["dic_path"]
        self.assertTrue(d.is_dir())
        for name in ("README.md","REQUESTS.md","PLAN.md","ARCHITECTURE.md","TEST_MATRIX.md","MANIFEST.json"):
            self.assertTrue((d/name).is_file(),name)
        self.assertIn("Prompt graph",(d/"PLAN.md").read_text())

    def test_custom_dic_view_is_first_class_and_flat(self):
        _,ids=self.plan(1); ph=ids[0]; self.s.create_dic(ph)
        rel=self.s.add_dic_view(ph,"THEOREM_MAP","# Theorem map\n",required=True)
        self.assertTrue((self.root/rel).is_file())
        with self.assertRaises(WorkflowError): self.s.add_dic_view(ph,"nested/BAD.md","x")
        self.assertTrue(self.s.recover()["ok"])

    def test_eps_instantiates_parallel_prompt_nodes(self):
        _,ids=self.plan(1); ph=ids[0]; self.s.create_dic(ph)
        eps=self.s.generate_eps(ph,[
            {"id":"P11A","operation":"positive derivation","parallel_group":"B1","subagent":True},
            {"id":"P11B","operation":"counterexample attack","parallel_group":"B1","subagent":True},
            {"id":"P12","operation":"merge","depends_on":["P11A","P11B"]},
        ])
        st=self.s.load(); phase=st["plans"][st["active_plan_id"]]["phases"][ph]
        obj=json.loads((self.root/phase["eps_paths"][eps]).read_text())
        self.assertEqual([n["id"] for n in obj["nodes"]],["P11A","P11B","P12"])
        self.assertEqual(obj["nodes"][0]["parallel_group"],"B1")
        self.assertTrue((self.root/obj["nodes"][0]["prompt_file"]).is_file())

    def test_optional_lanes_are_lazy_and_toggleable(self):
        pid=self.s.create_plan("Lanes","x"); ph=self.s.add_phase("P","x",lane_policy={"minor":"off","research":"on"}); self.s.approve_plan()
        base=self.s.runtime/"plans"/pid/"phases"/ph
        self.assertFalse((base/"minor").exists()); self.assertTrue((base/"research").is_dir())
        with self.assertRaises(WorkflowError): self.s.materialize_lane(ph,"minor")
        self.assertIn("verification",self.s.materialize_lane(ph,"verification"))

    def test_reports_always_flat_capped_and_raw(self):
        _,ids=self.plan(1); ph=ids[0]; self.s.create_dic(ph); eps=self.s.generate_eps(ph,[{"id":"P01","operation":"run"}]); self.s.start_phase(ph)
        self.s.record_action(ph,eps_id=eps,prompt_node_id="P01",action="run",result="raw-value",evidence_paths=["x.json"])
        st=self.s.load(); phase=st["plans"][st["active_plan_id"]]["phases"][ph]; r=self.s.runtime/"plans"/st["active_plan_id"]/"phases"/ph/"reports"
        self.assertTrue((r/"REPORT.md").is_file()); self.assertTrue((r/"RAW_RESULTS.jsonl").is_file()); self.assertTrue((r/"MANIFEST.json").is_file())
        row=json.loads((r/"RAW_RESULTS.jsonl").read_text().splitlines()[0]); self.assertEqual(row["result"],"raw-value"); self.assertEqual(row["prompt_node_id"],"P01")
        (r/"nested").mkdir(); rec=self.s.recover(); self.assertFalse(rec["ok"]); self.assertTrue(any("flat" in e for e in rec["errors"]))

if __name__=='__main__': unittest.main()
