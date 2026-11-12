# Project setup playbook

Apply to a new project or improve the missing pieces in an existing one. First
identify the product type, language, dependencies, UI, deployment target and
current workflow. State consequential choices briefly and proceed within scope.
Do not create every possible file or tool below just because it is listed.

## README and supporting documentation

Make README the entry point: what the project does, who it serves, current status,
requirements and the shortest working quick start. Explain where source, tests,
configuration and generated output live. Show the Make commands people will use.
Document environment variables with safe examples, not real credentials.

Add separate architecture, development, operations or release documents only when
the detail warrants them; link them from README. Record non-obvious decisions and
trade-offs near their implementation or in a short decision record. Include
troubleshooting for actual failure cases and honest limitations. For an interface,
add representative screenshots when they help someone understand the product,
using a repeatable capture command and sanitized fixtures.

Keep AGENTS.md short and portable: architecture, commands, test expectations,
modification boundaries, generated files and release permissions. It should
reflect the same workflow humans and CI use, not establish another build system.

## Nix and dependencies

Prefer Nix to ad hoc global installation in Jake's projects. Preserve a working
shell.nix or flake. A simple development shell may be enough for a small project;
a flake can be useful when locked inputs, reusable dev shells, packages or checks
serve a concrete need. Do not migrate an existing shell just to add a flake.

Declare language tools, formatter/linter, native compiler/linker dependencies,
service clients and applicable screenshot tools. Keep application dependencies
in their native manifests and lockfiles. Document supported platforms and versions.
Make setup either prepares the declared environment or validates it with actionable
instructions; do not let it succeed while required tools are absent.

Pin inputs where reproducibility matters. An unpinned channel, overlay or latest
image is a limitation to record, not a reproducibility guarantee. Test the quick
start with declared dependencies rather than relying on the author's global PATH.
Use existing uv/Cargo/Go/npm/pnpm workflows; Nix need not replace their manifests.

## Docker and Compose

Use Compose for an API's database/queue, integration testing or a concrete demo;
use a Dockerfile where container deployment/distribution is actually needed.
A library or CLI with no dependent service may need neither.

Keep the stack minimal, use appropriate image versions, configure through safe
environment examples and document state/volume ownership. Restrict local admin
ports appropriately. Use meaningful health/readiness checks and wait for actual
readiness in integration tests. Check shutdown, error logs and cleanup. Explain
which commands destroy test volumes; never remove unrelated containers or data.
Reuse existing services instead of adding a second database or monitoring stack.

## Native tests and quality gates

Choose tooling from the project, not from the example baseline:

| Project | Typical native building blocks |
|---|---|
| Go | go.mod/go.sum, gofmt, go vet, go test and go build; test with -race when relevant and supported |
| Python | Existing uv/pyproject or dependency workflow, pytest/unittest, Ruff or established formatter/linter; package only when distribution calls for it |
| Rust | Cargo manifests/locks, rustfmt, Clippy, cargo test/build; cargo package for libraries when relevant |
| Web/JavaScript | Existing package scripts and lockfile, unit/integration tests, browser tests for important user flows |
| Polyglot | Delegate to per-component native commands through the root Makefile |

Run real assertions, including failure cases, regression coverage and integration
boundaries that matter. Keep fixtures deterministic and isolate state, services,
ports and cleanup. Avoid a coverage percentage or a large CI matrix as a substitute
for useful tests. Don't rewrite working tests to match a scaffold. For visual
interfaces, use the visual workflow in addition to these behavioral checks.

## Seed data and benchmarks

For demos and data-backed tests, provide representative synthetic data, explicit
seed/load commands, documented repeat behavior and cleanup limited to owned test
state. Keep test fixtures isolated; tests must not depend on a manually seeded
demo database. Use stable data for screenshots and exercise a real workflow after
loading it. Never copy customer data or secrets into fixtures.

Add benchmarks for meaningful performance/evaluation questions. Validate correctness,
use reproducible workloads, record environment/source/configuration, repeat runs
and retain raw measurements. Reuse native tools and expose practical seed/demo/
bench commands through Make when applicable. Keep large or paid runs explicit;
don't add noisy CI thresholds or claim improvement from one run. See
[data and benchmarks](data-and-benchmarks.md) for loading/reset semantics,
measurement boundaries and comparison integrity.

## CI/CD and release

CI should enter/provision the documented environment and call make setup,
make check and make build as applicable, rather than maintain copies of commands.
Choose the minimum useful matrix for supported platforms/runtime versions. Match
local formatter/tool versions to CI and keep generated checks predictable.

Define what constitutes a release for this product: binary/package, source bundle,
container, website or deployed service. Choose a single version source, meaningful
release history and artifact/deployment checks. Reuse an established CalVer or
SemVer policy. Preparation should be reviewable before externally visible actions.
A release job must run release-check before publication; an ordinary test job
need not create or publish a release. Document required credentials safely,
partial failures and product-appropriate recovery. See release-management.md.

## Completion walkthrough

Can a new engineer follow README to enter the environment, run the app or tool,
load applicable demo/test data, run tests, make a small change, inspect its UI
if any, run a useful benchmark where relevant, and prepare a release?
Exercise the relevant path. Report missing services, unsupported platforms or
checks you could not run instead of treating generated files as completion.
