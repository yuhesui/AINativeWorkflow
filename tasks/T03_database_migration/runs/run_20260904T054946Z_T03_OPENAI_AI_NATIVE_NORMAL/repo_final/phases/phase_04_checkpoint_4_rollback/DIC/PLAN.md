# Checkpoint 4 Execution Graph

`P09` implements rollback history, reversal behavior, and visible cumulative tests. `P10` independently runs the wrapper suite and records an `accept`, `repair`, `replan`, or `escalate` disposition. The nodes are serial because they modify and verify the same CLI/history surface.
