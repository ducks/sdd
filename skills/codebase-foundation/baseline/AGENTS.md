# Engineering boundaries

src/lib.rs contains arithmetic; src/main.rs is the CLI. Preserve overflow
rejection and exit code 2. Use make help, make check and make build; review
RELEASE.md before make release-check or make release. Keep Cargo.lock committed.
Do not edit tests to conceal regressions. Only target/ and dist/ are generated.
Do not delete user files or widen cleanup. Release commands prepare local files;
commits, tags, pushes, GitHub Releases and registry publication require explicit
user authorization. No model, agent runtime or external service is required.
