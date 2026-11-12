# Repository research and design choices

Inspected local checkouts whose origin URLs match the requested public repositories.
The revisions and hashes below identify observed files; no project commands or release
workflows in those repositories were executed. Working checkout observations are not
a claim that all remote branches or historical releases have been audited.

| Repository | Observed revision | Actual conventions |
|---|---|---|
| [beanledger](https://github.com/ducks/beanledger/tree/d0e39f02f6f7756392142ad3171b26e35cc672f8) | `d0e39f02f6f7` | Svelte/Node/pnpm application, PostgreSQL and Docker integration tests. Different dotted CalVer YYYY.MM.DD.X in package.json. make check runs type checks, unit and E2E suites; release depends on check, then version edit/commit/merge/tag/push. CI and release workflows repeat native commands. Release waits for tests and bundles build, dependencies, migrations and scripts. shell.nix declares Node 22/Postgres/Docker/pnpm. |
| [claux](https://github.com/ducks/claux/tree/b40f4528903436662a68c8c81ad88514f16b85cb) | `b40f45289034` | Rust/Cargo; CalVer YYYYMMDD.0.X, native Cargo commands, lint combines formatting/Clippy/tests. shell.nix selects latest stable through an unpinned overlay. Make release has commit/merge/tag/push/cargo-publish side effects. Tag workflow builds Linux/macOS/Windows executables, per-asset SHA256 and combined SHA256SUMS. CI has deterministic contract tests and platform tests. |
| [diffuse-labs-test](https://github.com/ducks/diffuse-labs-test/tree/e63d7cb9ebfec2f4220318b00c865db24c6c4c5f) | `e63d7cb9ebfe` | Python 3.12+/uv, Harbor 0.25.0, uv.lock and hash-pinned Nix source. Task/control evidence and reproduction commands in README/VALIDATION. No root Makefile or release workflow found. A source/task-package release is more appropriate than inventing a binary/registry release. |
| [llm-mux](https://github.com/ducks/llm-mux/tree/f56698b3993c6faee369b3ecb2619277764a1175) | `f56698b3993c` | Rust/Cargo; CalVer YYYYMMDD.0.X. Make targets delegate to Cargo; release mutates branches/commits/tags/remotes and publishes crates. shell.nix supplies rustup and native dependencies without fixing the selected Rust version. Release workflow pins 1.94.1, requires a fmt/test/all-target Clippy quality job before five-platform builds, then generated GitHub release notes. No checksum step in inspected workflow. |
| [murmur](https://github.com/ducks/murmur/tree/e72d8216682666a13bd22650f5ffc2f133b599ad) | `e72d82166826` | Dependency-free Rust experiments plus a Python research toolkit. Cargo version 0.1.0, shell.nix with Rust/Cargo/Python; README explicitly notes unpinned Nix channel and records seeds/experiment limits. No root Makefile or GitHub release workflow found. No established binary publication strategy inferred. |
| [replaybook](https://github.com/ducks/replaybook/tree/294001ec423af74e315aade2bf1c7a3cd6a9b8e2) | `294001ec423a` | Rust/Cargo; CalVer YYYYMMDD.0.X selected from local v-tags; Make build/test/fmt/clippy and specialized host/Harbor/pages gates. lint aggregates gates. shell.nix pins Rust 1.88 through an unpinned overlay URL. Release Make recipe branches, edits Cargo.toml, commits, merges --no-ff, tags, pushes and cargo publishes. Tag CI builds four platform artifacts, then SHA256SUMS and generated GitHub notes. |

## Reuse and deliberate differences

Reuse native build tools under a discoverable Make interface, lockfile consistency,
release quality gates, versioned source identities, meaningful notes, supported
artifacts and independently verified checksums. Preserve an existing CalVer policy;
the small new Rust reference uses SemVer because it has no prior release contract.
Neither is presented as a universal rule.

Do not copy error suppression (`cargo check ... || true`) in the inspected version
bump recipes, or their combined preparation/publication boundary. The requested
contract adds a mandatory check alias and release-check, with local release
preparation separated from explicit publication approval. Existing projects are
not edited by this work. A project-specific adapter can preserve its established
publish implementation behind the authorization boundary rather than replacing it.

The inspected Rust repositories do not all have a hand-maintained changelog.
Replaybook and llm-mux generate GitHub release notes; that is existing release
history, not evidence of a local changelog check. The baseline intentionally uses
a small human-written CHANGELOG.md so readiness is locally testable. No historical
notes have been invented. BeanLedger legitimately needs its dependent-service E2E
environment; the dependency-free CLI does not need containers or a matrix.

Nix is retained as shell.nix. The new baseline and SDD environment pin an existing
known Nixpkgs source/hash, and setup reports actual tool versions. CI independently
tests Python 3.12/3.14 and Rust 1.94.1. Pinning Nixpkgs is a reproducibility choice,
not a claim that a Nix package and CI toolchain produce identical binaries.

## Architectural boundary

An ordinary SKILL.md routes to focused references. There is one small Rust CLI
baseline, a local preparation helper and an independent Python verifier. No agent
runtime, package registry, generator DSL, dependency resolver or model integration.
A helper supports this repository's source bundle as well as the CLI archive;
it is explicitly not a universal packaging system. Other languages reuse the
contract and existing tools, with appropriate native probes before claiming
runtime verification. The verifier recognizes partial native layouts and uses
UNKNOWN when recognition is insufficient.

[Machine-readable repository observations](evidence/foundation/repository-observations.json)
contain per-file hashes. External evaluation and observed limits are in
[the audit report](codebase-foundation-audits.md).
