# SDD source releases

VERSION is the authoritative SemVer source. This is a collection of portable
skills, not a PyPI package or binary product. Write truthful CHANGELOG.md notes
for the version being prepared. Tags use vVERSION. No release is being published
as part of implementing this capability.

Run `make setup`, `make check`, `make build`, `make release-check`, then
`make release`. Check runs Python/worker/foundation tests. Release-check additionally runs all
Docker-backed monitoring acceptance and negative controls, requiring an authorized
Docker daemon. Use SDD_ISOLATED_DOCKER=1 with nix-shell when host plugins conflict;
that creates only a disposable public-fixture client configuration.

Build creates dist/sdd-source.tar.gz containing the maintained skill directories,
examples, verification scripts and documentation; caches, local runs and build
products are excluded. Local release preparation checks the source VERSION,
changelog, license, docs and built source bundle, records the source Git HEAD and
creates dist/sdd-0.1.0.tar.gz with manifest.json and SHA256SUMS. VERSION owns the
release number; the filename in this explanation is an example, not a second
version source. Archive members and contents are checked after creation. Stable
member order/metadata and gzip headers permit repeatable source bytes for the
same file contents. No binary reproducibility or signing is claimed.

A clean checkout and unused vVERSION tag are required. For a reviewed local
preview of uncommitted work only, RELEASE_ALLOW_DIRTY=1 prints the dirty paths
and labels the manifest as a preview. Never represent it as a clean release.
An exported source tree requires an explicit RELEASE_SOURCE_ID snapshot identity;
this is operator-provided, not verified Git provenance.

Make release never commits, tags, pushes, creates GitHub Releases or publishes.
Review the local archive, manifest and checksums before requesting explicit
approval for any of those operations. GitHub authentication is NOT APPLICABLE to
local preparation; safely check it only before approved publication, without
printing tokens. Once authorized, tag the reviewed clean commit with vVERSION,
push it and attach the matching archive/checksum file to a GitHub Release.
No tag-triggered publication workflow is introduced.

On a test/build failure, preparation stops. Fix it and rerun. On an archive or
checksum failure, inspect partial files and rerun local preparation; do not upload
an unchecked pair. If a tag exists, inspect its commit and artifacts and choose a
new version if needed, never move it automatically. After partial GitHub publication,
inspect remote state and upload only missing assets for the same source after
approval. Do not overwrite published artifacts with different bytes. This project
has no service rollback or package-registry withdrawal operation. Consumers can
restore a previously verified skill snapshot; deletion of a Git tag does not
revert their installed copies.
