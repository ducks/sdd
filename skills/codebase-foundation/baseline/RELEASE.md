# Releases

Cargo.toml is the authoritative SemVer source. Cargo.lock must agree. Update the
version intentionally and write a meaningful matching CHANGELOG.md section;
do not infer or fabricate notes from a proposed version. Tags use vVERSION.

Run `make check`, then `make release-check`, then `make release`. The last two
require a clean Git tree and a resolvable HEAD. An existing vVERSION tag blocks
preparation. No command creates commits, tags, pushes, uploads or publishes.
For a reviewed development preview only, set RELEASE_ALLOW_DIRTY=1; the script
prints the dirty paths and marks the manifest as a dirty preview. An exported
source tree without Git requires RELEASE_SOURCE_ID identifying its reviewed
snapshot; this is operator-supplied provenance, not a verified Git commit.

The local dist/foundation-demo-VERSION.tar.gz contains the host binary, license,
README, changelog and a manifest recording source revision and dirty state.
SHA256SUMS verifies the archive; packaging validates member names, mode and the
binary's behavior before reporting success. Source files are not bundled with
this executable distribution. Builds are not claimed byte reproducible across
toolchains/platforms. Output identifies the actual Rust toolchain.

Publication is a separate, manually authorized operation. Review artifacts,
checksums, source commit, version and platform first. Only after explicit user
approval: create an annotated vVERSION tag on that commit, push it, and create a
GitHub Release attaching the archive and SHA256SUMS. There is no automatic tag
workflow in this baseline. Publishing credentials are NOT APPLICABLE to local
preparation; before authorized publication verify GitHub authentication without
printing tokens. A library adapter should also run cargo package --locked and
cargo publish --dry-run; this binary demo does not publish to crates.io.

If tests, metadata or builds fail, preparation exits nonzero before packaging.
An artifact failure leaves no success marker; fix it and repeat preparation.
The archive is replaced atomically; a checksum-write failure requires rerunning
and verifying the pair. An existing tag must be investigated, never moved by
this workflow. If publication partially succeeds, inspect remote assets and
checksums and finish missing uploads for the SAME source commit only after
approval. Do not overwrite an asset with different bytes under the same release.
A published crate cannot generally be withdrawn: yanking and a new version differ
from deletion. A service adapter must record deployment identifiers and migration
compatibility before recommending rollback. This CLI can be restored by installing
a previously verified binary; Git tag removal is not deployment rollback.
