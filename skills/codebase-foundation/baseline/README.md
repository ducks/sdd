# Foundation demo

A dependency-free Rust CLI: `target/release/foundation-demo 7` prints `14`.
Invalid or overflowing input exits 2. `--version` reports the compiled Cargo version. Rust owns arithmetic and argument handling;
`scripts/release.py` owns local packaging. No network service, secrets or database.

## Development

Supported: Unix, Python 3.12+, Rust/Cargo 1.80+, GNU Make, a C linker (`cc`) and Git. Enter
`nix-shell` for the pinned Nix package set (its toolchain can differ from CI 1.94.1;
`make setup` reports actual versions). Or supply those tools yourself.

- `make help`: documented commands.
- `make setup`: validate tools, no downloads or global installations.
- `make format`: rustfmt.
- `make lint`: format check and Clippy.
- `make test`: Rust tests, including overflow and negative input.
- `make check`: local quality gate.
- `make build`: locked, offline optimized build.
- `make clean`: remove only Cargo's owned target directory, rejecting symlinks.
- `make release-check`: quality gate, build and release metadata validation.
- `make release`: prepare a local archive and SHA256SUMS, then verify contents.

If Cargo reports a missing dependency, inspect Cargo.lock and intentionally fetch
it in an authorized environment. This reference has no external crates. Do not
remove --locked to hide lock drift. For formatting failures run make format.
For overflow errors pass a smaller integer. There is no daemon to restart.

## Limitations

Only the host binary is packaged. No cross-platform builds, registry, installer,
signing, provenance or deployment. See [RELEASE.md](RELEASE.md) for release and
recovery procedures. MIT licensed; preserve LICENSE when adapting.
