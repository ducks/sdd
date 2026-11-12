# Observable contract

The foundation is the project's working development and delivery workflow, for
both new and existing software. It is not defined by the bundled Rust example or
by a score from the optional checker. Use native project evidence.

README should explain purpose, quick start and where to find architecture,
configuration, development, testing, troubleshooting and delivery instructions.
A declared development environment (preferably existing Nix conventions for
Jake's projects) should support those commands. Include Docker/Compose when it
serves actual dependencies/deployment. UI/TUI changes need a repeatable screenshot
and interaction workflow; headless projects do not. CI/CD should reuse the local
interface and distinguish quality gates from external publication/deployment.

Where data is needed, synthetic demo seeds and isolated test fixtures must load
repeatably with documented, safe reset semantics. Applicable benchmarks need
correctness checks, reproducible workloads, actual measurements and recorded
comparison conditions; they are not mandatory infrastructure for every project.

A complete foundation has a root Makefile implementing help, setup, format, lint,
test, check, build, clean, release-check and release. Each target performs its
named operation or explicitly states a justified not-applicable outcome. Test,
check and release-check cannot claim verification from no work. Use exit 0 for
executed success, nonzero for failure; a verifier's incomplete outcome uses 2.
The verifier's report states are PASS, FAIL, SKIP, UNKNOWN, NOT APPLICABLE.
Do not confuse NOT APPLICABLE with an executed passing check.

The stable gate is make check. CI reuses it. A real test runner discovers a
nonzero suite; injecting a failing test makes make test and make check fail.
Release preparation runs that gate and a build, checks the authoritative version,
lockfile, truthful changelog, source revision/tree state, documentation and
expected artifacts. Packaging is inspected independently. Identical reviewed
inputs should produce equivalent outputs; measure byte reproducibility before
claiming it. Toolchain/platform differences may prevent binary reproducibility.

Release preparation is local and separate from publication. Default invocation
never commits, tags, pushes, publishes, deploys or edits remote releases. Existing
publishing scripts may remain behind an explicit authorization gate, but an
agent must not supply that gate without actual user approval. A dry-run flag is
not evidence if its implementation still publishes. Review direct and indirect
commands. Documentation covers failed tests/builds, existing tags, partial
publication and product-appropriate recovery.

Clean removes only declared generated paths, rejects path/symlink escape and
preserves source, secrets and user data. Setup declares required tools and does
not rely on the author's accidental global environment. Platform support and
unpinned sources are stated honestly. An applicable license, ignore rules and
dependency policy are part of assessment; legal or supply-chain conclusions are
not established by simple file checks.

Audit inventory does not certify engineering quality. The supplied executable
checker supports a reviewed Rust baseline and partial native layout recognition;
other projects need reviewed probes for their actual runners and release process.
