# Applying the foundation playbook

## Existing projects

Inspect architecture and the existing developer path first. Run relevant original
checks under the executing environment's authorization. Keep working native tools,
component boundaries and deployment choices. Improve README, environment, Make,
tests, visuals, CI or release behavior in the requested scope. Documentation and
configuration may need editing; application source should change only when the
requested foundation work requires it. Check original behavior after changes.

For example, an existing Go service may need documented Compose database startup,
a Nix development shell and Make aliases over its existing Go tests. That does
not call for a Rust binary, a Python package, a second database or a new queue.
An existing Python service using uv should retain its project/lockfile and
framework, with Make delegating to the actual test/build commands. Neither
requires a new repository or the bundled baseline.

## New projects

Choose the minimum coherent setup for the language and product. Establish its
native manifest/source structure, README quick start, appropriate Nix environment,
Make interface, useful tests, CI and release process. Add containers for actual
services or deployment, and a screenshot workflow if it has a visual interface.
Start from the intended application's requirements, not by copying the Rust
example. Verify the documented developer path in a fresh workspace/environment.

## Language and product differences

- Go: preserve modules, go.sum and existing commands. Use native formatting,
  vet/test/build; exercise concurrency and dependent services where relevant.
- Python: preserve uv or the established environment, native test discovery and
  framework conventions. Packaging, service deployment and standalone scripts
  have different build/release needs.
- Rust: preserve workspace/version inheritance and lockfile policy. Use Cargo,
  rustfmt and Clippy, with native package checks for libraries where relevant.
- Web/JavaScript: keep the existing package manager/scripts and lockfile; connect
  browser/visual checks to the actual app and its fixtures.
- Services: document config, state, health, logs, shutdown, deployment and recovery.
  Use specialized monitoring/worker skills only for applicable work.

Read project-setup.md for the workflow and visual-workflow.md for screenshots.
Scoped work such as tests,docs,release does not authorize an architecture rewrite.
Report outstanding obligations instead of expanding scope silently.

## Optional executable example

baseline/ is a tested Rust CLI illustration of a Make/release workflow, with
bootstrap/improve fixtures in tests/test_foundation.py. It is not a starter for
all projects. Its release helper assumes that CLI's behavior and needs adaptation
before reuse in a different application.

verify/run.py optionally inventories files without execution. Its --allow-exec
mode runs supported probes in disposable copies after authorization. That checker
has limited native-layout coverage and no complete Go/Python, visual or CI/CD
assessment. The target's own tests, startup, screenshots and release checks are
normally the evidence to use. Unsupported checker probes are not a reason to
change a correctly working project or to consider the skill unusable.
