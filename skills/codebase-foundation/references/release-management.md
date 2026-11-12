# Release preparation and publication

Inspect the actual release flow before calling it. Strong patterns in the named
repositories include native Cargo commands, tag-triggered per-platform artifacts,
checksums (Replaybook/Claux), release quality dependencies (llm-mux/BeanLedger),
lockfiles and explicit source versions. Their Make release commands currently
combine version edits, commits, merges, tags and pushes; do not copy that side
effect boundary into an unauthenticated local preparation command. See the
repository-specific evidence in docs/codebase-foundation-research.md.

Preserve established version policy. Cargo.toml, pyproject.toml, package.json or
VERSION should own the value, with lock/package metadata agreeing. Existing
CalVer need not become SemVer. Tag-derived versions are legitimate when builds
from exported source have a defined fallback. Tags use the project's established
convention; the baseline uses vVERSION. A clean or explicitly understood source
state and exact revision must be recorded before release artifacts are approved.

Release-check needs: complete local gate, build, truthful notes, version/lock
consistency, documentation and expected package contents, checksum/archive tests,
and relevant publication prerequisites safely checked. Dependencies unavailable
locally mean SKIP/UNKNOWN, not success. Do not print credentials. Registry login
and production access are not required for local source or CLI preparation.

Binary: package only supported platform artifacts, preserve executable mode and
verify --version or equivalent behavior; checksum actual bytes. Library: use
native package inspection and registry dry-run, not only a cargo build. Service:
version immutable image/artifact/source and deployment record, validate config,
health, migrations and rollback compatibility. Experiment: record code, inputs,
seeds and toolchain; no invented package registry requirement.

Review local artifacts/metadata before requesting publication approval. An
existing tag is not permission to replace it. On failures stop, retain useful
evidence and retry only the missing stage with the same source identity. Inspect
remote state after partial publication; do not blindly rerun mutating commands.
A yanked crate still exists; a new version may be needed. A Git tag rollback does
not revert running services or database migrations. Signing/provenance are
optional until justified and implemented, never claimed from planned workflows.
