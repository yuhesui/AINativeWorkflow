# MINOR.md — Optional Phase-Local Minor Lane

Minor is a bounded local-maintenance capability. In v5.6.35 it is **not required to exist in every Phase**.

Canonical lane policy:

```text
minor=off   prohibit Minor work for the Phase
minor=auto  default; create the lane lazily on first Minor request
minor=on    materialize/maintain it from Phase initialization
```

Suitable work includes links, headings, stale filenames, status/index synchronization, small documentation/test-expectation repair, and concise extraction from existing evidence.

Promote rather than treat as Minor when the request changes architecture, public API/dependencies, scientific method or claims, frozen experiment protocol, data policy, release/submission state, credentials/external actions, destructive behavior, or Phase acceptance.

The compatibility `aw minor ...` commands lazily materialize the legacy phase-local Minor workspace when required. In the canonical hierarchy, the Phase lane itself is governed by the `off|auto|on` policy recorded in state.
