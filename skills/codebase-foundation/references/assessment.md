# Choose the right foundation

For setup or improvement, use this to select the right work; an audit is only one
way to use the skill. Briefly explain important choices rather than turning every
small change into a checklist report. For each relevant capability identify its
classification, existing implementation and smallest useful action. REQUIRED
is an obligation for this project, RECOMMENDED improves it, OPTIONAL is justified
but unnecessary now, NOT APPLICABLE needs a project-specific reason.

| Capability | Rust CLI/library | Stateful Python API | ML experiment |
|---|---|---|---|
| Root Makefile and release strategy | REQUIRED | REQUIRED | REQUIRED |
| Tests, regression and failure paths | REQUIRED | REQUIRED | REQUIRED; deterministic seeds and baselines |
| Seed/demo data | Small representative inputs when useful | REQUIRED for data-dependent tests; demo seed RECOMMENDED when useful | REQUIRED reproducible inputs and data versions |
| Benchmarks | RECOMMENDED for important performance paths | RECOMMENDED for meaningful latency/throughput questions | REQUIRED for experiment/evaluation claims |
| Build/package validation | REQUIRED | REQUIRED | REQUIRED for code and versioned experiment outputs |
| Environment/locks | REQUIRED; Cargo.lock policy distinguishes binary vs library | REQUIRED; declared dependency resolution and DB version | REQUIRED; seeds, data/model versions, toolchain |
| Documentation and troubleshooting | REQUIRED | REQUIRED | REQUIRED; limitations and reproducibility |
| Docker/Compose | NOT APPLICABLE unless real integration need | RECOMMENDED for dependent services, preserve existing alternatives | OPTIONAL for GPU/runtime needs |
| Health, logs, metrics, shutdown | CLI errors REQUIRED; daemon checks NOT APPLICABLE | REQUIRED | OPTIONAL unless serving |
| Registry/GitHub binary publication | OPTIONAL; choose actual distribution | OPTIONAL; deployment records may suffice | OPTIONAL; source/experiment release may suffice |
| CI matrix/signing/provenance | RECOMMENDED only for supported platforms/risk | Context dependent | Context dependent |
| AGENTS.md | RECOMMENDED; short, portable and accurate | RECOMMENDED | RECOMMENDED |
| Screenshots/visual verification | REQUIRED for a TUI; otherwise NOT APPLICABLE | REQUIRED if it has a UI; otherwise NOT APPLICABLE | Only for visual outputs/interfaces that matter |

Inspect discovered tests/assertions, concurrency, failure isolation, cleanup,
secrets/configuration, lock constraints, license and generated outputs. Never
recommend Docker merely because the checker recognizes Compose. Nix is preferred
for these personal projects; an existing reliable environment in an unfamiliar
repository is evidence to preserve, not a migration request.

Version mismatches can be intentional during development (Unreleased vs latest
tag). Record this policy, not an automatic demand to rewrite upstream history.
For dynamic versions, workspaces, included Makefiles, tox/nox/task runners or
non-GitHub CI, manual review/probes can supersede a checker's UNKNOWN. Confirmed
false positives should be documented, not hidden or asserted away.

Go and Python are ordinary target languages, not unsupported uses of the skill.
A Go CLI/service uses the same foundation decisions with Go modules and native
tooling; Python uses its existing uv/pytest/unittest or other established setup.
The optional Rust checker's coverage is narrower than this playbook's scope.
For a browser app, include a repeatable screenshot/interaction workflow; for a
headless service, focus instead on API, state and operational verification.
