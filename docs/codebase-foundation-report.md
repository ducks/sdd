# codebase-foundation implementation report

## Playbook refocus

Following user clarification, SKILL.md now leads with setting up or improving new
and existing projects using Jake's conventions: README/documentation, Nix
shell/flake, Make, appropriate Docker/Compose, native Go/Python/other tests,
screenshot/visual workflows, CI/CD and releases. The Rust baseline and checker
are optional supporting examples, not the skill's scope or required execution
path. Bootstrap no longer directs the agent to copy a Rust application.

New project-setup.md and visual-workflow.md cover those decisions. Visual guidance
uses observed BeanLedger Playwright dark/light/mobile captures and Claux tuishot
snapshots without claiming all projects use either mechanism. Existing project
commands and actual image inspection remain the evidence to use.

This revision changes instructions/documentation only. The runtime results and
source-hash index below describe the prior example implementation validation;
they are not fresh runtime evidence for these broader instructions. They do not
prove an arbitrary Go/Python setup, screenshot workflow or deployed CI/CD system.

Implemented on feature/codebase-foundation. No commits, tags, pushes, registry
publication, GitHub Releases or deployments were performed. External audits
were read-only. Existing monitoring/worker application and verifier source was
preserved; root development/CI integration changed.

## Implemented

- Portable SKILL.md with audit, improve and bootstrap modes and scoped requests.
- Focused assessment, contract, Makefile, release and adaptation references.
- Dependency-free Rust CLI baseline: checked arithmetic, overflow failure,
  Cargo.lock, rustfmt/Clippy, meaningful tests, Make interface, pinned shell.nix,
  CI, license, architecture/development/troubleshooting docs and AGENTS.md.
- Local release helper: authoritative Cargo/SemVer or SDD VERSION, changelog and
  lock consistency, dirty-tree/unused-tag guards, source identity, built behavior,
  deterministic archive metadata, checksums and package contents verification.
  It never performs publication or Git mutations. Publication remains separately
  authorized and documented, with failure/partial-publication recovery guidance.
- Independent Python verifier with machine-readable PASS, FAIL, SKIP, UNKNOWN,
  NOT APPLICABLE. It performs static inventory without running Make, then optional
  bounded commands in disposable copies. Real test discovery, injected failures,
  release metadata mutation, archive/checksum/source checks and cleanup tripwires
  are exercised. Reviewed helper matching enables local release probes; alternative
  implementations need native probes and remain UNKNOWN, not declared defective.
- Root Make setup/format/lint/check/build/clean/release-check/release targets,
  dedicated foundation controls, CI integration, pinned Nix tools and Ruff hashes.
  Existing capability targets remain available. Root release-check includes live
  monitoring checks and negative controls as well as the non-Docker gate.

The ten mandatory targets are help, setup, format, lint, test, check, build,
clean, release-check and release. Native tooling performs the work. check is the
local non-Docker gate; release-check additionally verifies live monitoring for
this multi-capability distribution. The Rust CLI's gate requires no Docker.

## Observed verification

- Full local make check passed: 26 Python tests (including 13 foundation tests),
  syntax/style checks, both worker examples and both worker negative controls.
- Foundation bootstrap and improve each passed 29 checks, with 1 justified
  NOT APPLICABLE (containers), 0 FAIL, 0 SKIP and 0 UNKNOWN.
- Eleven deliberately defective fixtures were rejected: seven static controls
  and four behavioral controls. These include all ten requested cases plus
  lockfile drift. Failure messages inside those controls are expected evidence.
- The alternative native test recipe passed. An unfamiliar release helper was
  reported UNKNOWN, rather than rejected for differing from the reference.
- Bootstrap runs in a fresh exported source snapshot, with explicit source ID;
  no commit is created. Improve preserves legacy src/, tests and manifest bytes,
  adds only engineering files and retains an existing Make alias. No containers
  or new framework are introduced into that application.
- Monitoring baseline and adapted Flask example each passed 19/19 live checks;
  broken scrape, frozen counters and broken data source were each detected.
- Worker baseline and invoice example each passed 14/14 live checks; missing
  lease fencing and missing timeout were each detected.
- The reference also passed 29 checks plus 1 NOT APPLICABLE on Rust/Cargo 1.80
  with Python 3.12.5; the pinned development environment uses Rust 1.97 and Python
  3.12.14. The native host previously exercised Rust 1.94.1 and Python 3.14.7.
- The skill-creator quick validator reported “Skill is valid!”. This checks skill
  metadata/shape, not engineering behavior.
- Two fixed-revision external source audits ran without authorization to execute
  project code. All source file hashes remained unchanged. Both lack the required
  root Makefile; other unfamiliar conventions are reviewed rather than erased.
  See the separate audit report for counts, limitations and recommendations.

Machine-readable evidence is under docs/evidence/foundation/. Full local logs
and transient artifacts are under runs/ and /tmp/sdd-*.log, intentionally untracked.
The final command/result index records release preparation and source hashes.

## Commands

```sh
nix-shell --run 'make setup && make check && make build && make verify-foundation'
nix-shell --run 'make foundation-controls'
SDD_ISOLATED_DOCKER=1 nix-shell --run 'make verify-baseline verify-example controls'
nix-shell --run 'python3 /home/urho/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/codebase-foundation'
python3 skills/codebase-foundation/verify/run.py --project /tmp/click-REVISION --output /tmp/click-audit.json
python3 skills/codebase-foundation/verify/run.py --project /tmp/healthchecks-REVISION --output /tmp/healthchecks-audit.json
```

The audits were also invoked directly through the same audit() API to retain
fixed source provenance, inventory and before/after source hashes. See their JSON
source fields for actual paths/revisions, not the REVISION placeholders above.
A dirty working tree must be explicitly labelled a preview for local preparation;
clean release eligibility is not claimed while this requested work is uncommitted.

## Defects discovered and corrected

- The first execution limit allowed only 4 MiB per generated file, causing the
  Rust linker to fail on test binaries. It is now 128 MiB; wall time, output
  capture and process-group cleanup remain bounded. This was a verifier problem,
  not an application failure.
- An injected Rust test initially failed rustfmt before reaching its assertion.
  The injection now has native formatting, so make check demonstrably reaches
  the failing test. This prevents a false claim about test-failure propagation.
- Missing-tool command text in failed setup output was incorrectly counted as a
  tool declaration. Only successful setup evidence now contributes declarations.
- External audits exposed natural-language “make sure”/“make it” false positives
  and an incorrect regex interpretation of closing Markdown fences. Command
  examples now use a line-oriented fence parser and regression coverage.
- Local and CI formatters initially differed (old channel vs pinned package set).
  CI's hash-pinned Ruff now matches the actual Nix Ruff version, 0.16.4.
- Docker validation initially stopped before application startup because host
  plugins did not match the pinned client. An opt-in disposable Docker client
  configuration selects matching Nix plugins without changing user settings or
  loading registry credentials. The existing application checks then passed.

## Files

New: skills/codebase-foundation/{SKILL.md,references/,baseline/,verify/},
tests/test_foundation.py, scripts/foundation.py, pyproject.toml, requirements-dev.txt,
AGENTS.md, VERSION, CHANGELOG.md, RELEASE.md, docs/codebase-foundation-{research,audits,report}.md
and docs/evidence/foundation/ reports. Modified: README.md, Makefile, shell.nix,
.github/workflows/test.yml and .gitignore. The evidence index lists individual
files and hashes. Existing skill and application implementations were not rewritten.

## Limits and trade-offs

This establishes a useful foundation capability, not universal automatic auditing.
Static Make/shell/workflow recognition is conservative. Dynamic/workspace versions,
included Makefiles, tox/Flit/service releases and nonstandard test paths need review
and suitable native probes. File presence is reported as detection, not runtime
proof. External tests, deployments, signing and publication were not executed.
No claim of agent productivity or superiority follows from these fixture tests.

Copies, sanitized environment variables and timeouts are not a hostile-code
sandbox. Authorized commands retain operator filesystem/network permissions;
truly untrusted code needs an OS/container sandbox. Exact helper matching is a
safe execution boundary for the supplied local release tests, not a requirement
that another correct project copy its implementation. Full behavioral coverage
for arbitrary publishing/cleanup helpers remains unimplemented.

The bootstrap is verified from a clean exported snapshot rather than a newly
committed Git checkout: creating a commit is outside this task's authorization.
Dirty-tree and existing-tag guards have focused tests; no real tags are created.
The requested clean release path becomes available after a separately authorized
review/commit. The archive test establishes identical bytes for identical inputs,
not cross-platform Rust binary reproducibility. Hosted GitHub CI is configured
but has not run remotely. MSRV/platform claims beyond tested toolchains remain
limited to the documented profile.

Next steps: review the uncommitted diff, optionally authorize a commit and run
release-check on that clean source; use the skill on a real Python/service
improvement with reviewed native release probes. Do not expand automatic execution
or add scaffolding abstractions just to reduce UNKNOWN counts.
