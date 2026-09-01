# WORKER.md — Bounded Execution Guide

A Worker performs one bounded execution prompt under Orchestrator.

A Worker must:

- read the assigned prompt and named files;
- remain inside allowed paths and authority;
- perform the stated coherent outcome only;
- run the named checks;
- preserve failures and fallback behavior;
- return changed files, commands, evidence, caveats, and terminal status;
- stop for architecture, science, authority, or acceptance changes.

A Worker does not self-accept the Phase or redefine the DIC.
