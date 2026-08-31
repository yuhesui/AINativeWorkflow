# Qualification report

Status: **BLOCKED**


The complete PaperBench project was reconstructed with both `project/paperbench`
and its required `project/common` sibling.  Frozen dependency synchronization
succeeded.  An initial unit run produced 38 passed, 14 skipped, 4 failed, and
11 errors: the four failures were exclusively API-key-dependent SimpleJudge
tests and the errors were Docker-socket permission failures in the non-root
WSL invocation.  Both official Dockerfiles then built successfully, and the
root suite passed 49/49 with 18 API-judge cases deselected.  These checks are
recorded in `oracle_runs/`; they establish substantial execution machinery but cannot
qualify the native target grader or full target reproduction.  T7/T7m remain
BLOCKED because no approved grader credential is available and this Docker
installation lacks NVIDIA runtime support; the 6 GiB host GPU also cannot be
assumed sufficient for the frozen full reproduction.  No Code-Dev downgrade
was made.
