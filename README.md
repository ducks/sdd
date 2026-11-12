# Skill-Driven Development (SDD)

A small experiment in packaging an engineering capability as an ordinary
[Agent Skill](https://agentskills.io/specification): knowledge, a working
baseline, adaptation guidance and independent executable acceptance checks.

Three engineering capabilities and two interview practice skills are included:

| Skill | Working reference | Verification |
| --- | --- | --- |
| [monitoring-stack](skills/monitoring-stack/SKILL.md) | Python HTTP service, Prometheus and Grafana | Real scrape/query checks and broken-stack controls |
| [reliable-worker](skills/reliable-worker/SKILL.md) | Python/SQLite durable jobs with a process supervisor | Retry, duplicate, crash, timeout and shutdown checks |
| [codebase-foundation](skills/codebase-foundation/SKILL.md) | Project setup/improvement playbook following Jake's conventions | Native project checks and visual review; optional tested Rust example/checker |

| [frame-system-design](skills/frame-system-design/SKILL.md) | FRAME decision worksheet and rehearsal prompts | Review checklist; no automated design grader |
| [code-live-coding](skills/code-live-coding/SKILL.md) | CODE prompts, pacing and setup checklist | Guides actual test/metric verification; no bundled application verifier |

No agent runtime, model API or hosted service is required to load these skills.
The interview guides package knowledge and practice prompts; they do not claim
to be tested application baselines.

This is a packaging practice, not a new skill specification. Ordinary skills
already support scripts and assets. Scaffolding already produces working code.
The question here is whether keeping a tested baseline and runtime verifier
with adaptation guidance helps agents integrate capabilities into existing apps.
The same acronym also means Spec-Driven Development elsewhere; this project
does not replace that methodology. See [research and architecture](docs/research.md).

## Try monitoring-stack

Requirements: Python 3.12+, Docker Engine, Docker Compose v2+, and authorized
container execution. First image/package downloads need network access; deployed
services and checks run locally. `nix-shell` supplies Python dependencies and
Docker clients without installing tools globally; a Docker daemon is still needed.
If host Docker plugins conflict with the pinned clients, run
`SDD_ISOLATED_DOCKER=1 nix-shell` for matching plugins in a disposable client
configuration. It does not load your registry credentials and cleans up on exit.

```sh
nix-shell                         # optional, or use your Python environment
make test                         # Python unit/integration tests, no Docker
make verify-baseline              # builds, runs all checks, removes owned resources
make verify-example               # same checks against the adapted Flask service
make controls                     # deliberately broken fixtures must be detected
```

The baseline's only application dependency is prometheus-client. The Flask
example adds Flask and its pinned dependencies. Container images are digest
pinned and Python requirements have hashes. No code is downloaded and executed
by skill discovery. Review skill resources, target code and Compose volumes
before authorizing builds or tests. Skill instructions cannot grant permissions.

`runs/*.json` records PASS/FAIL/SKIP/UNKNOWN per check. Exit zero requires all
checks PASS. Missing Docker, skipped execution or blocked checks never imply
success. [Verification details](skills/monitoring-stack/verify/README.md).

To inspect the disposable demo manually:

```sh
cd skills/monitoring-stack/baseline
export GRAFANA_PASSWORD="$(python3 -c 'import secrets; print(secrets.token_urlsafe(24))')"
docker compose up --build -d --wait
# App: http://127.0.0.1:18000    Prometheus: http://127.0.0.1:19090
# Grafana: http://127.0.0.1:13000 (admin / your generated password)
docker compose down --volumes --rmi local
```

The demo publishes only loopback ports. Do not expose it publicly without the
application's appropriate authentication/network design. It uses ephemeral
monitoring data; production storage and retention are separate decisions.

## Try reliable-worker

Python 3.12+ standard library only; no Docker or broker needed:

```sh
make verify-worker
make verify-worker-example
make worker-controls
```

> Use the `reliable-worker` skill to make this job handler durable, bound retries
> and execution time, preserve its existing architecture, and verify duplicate
> delivery, worker crashes and graceful shutdown.

The skill accepts ordinary task options such as `language: auto`, `queue: auto`,
`storage: auto`, and `scope: full` or `handler`. Inspect/reuse existing workers
before choosing the reference. The SQLite implementation is tested locally;
other queues require appropriate adaptation and matching checks. It does not
promise exactly-once external side effects.

For a manual local example:

```sh
cd skills/reliable-worker/baseline
python3 worker.py --db /tmp/sdd-worker-demo.sqlite enqueue --key demo-1 --payload '{"message":"hello"}'
python3 worker.py --db /tmp/sdd-worker-demo.sqlite work --idle-exit 1
```

See [worker adaptation/results](docs/worker-adaptation.md) and the
[worker contract](skills/reliable-worker/references/contract.md). The invoice
example preserves the synchronous domain API/CLI while adding background jobs.

## Use codebase-foundation

Use this skill to set up a new project or improve an existing one using Jake's
engineering conventions. It guides README and architecture documentation, Nix
shells/flakes, Make commands, appropriate Docker/Compose, native tests, demo/test seed data, benchmarks, screenshot
workflows, CI/CD and release management. Go and Python are normal target projects;
there is no requirement to create a new repository or adopt Rust.

> Use codebase-foundation to improve this Python service. Preserve its architecture
> and uv setup; improve the README, Nix environment, Make targets, tests and CI.
> Reuse its Compose database. Define release preparation without publishing.

> Use codebase-foundation to bootstrap a Go project with a useful README, Nix
> environment, Makefile, native tests, CI and a safe release workflow. Add Docker
> only if it serves a concrete requirement.

For a UI/TUI, include a repeatable screenshot → inspect → change → recapture
workflow and behavioral checks, reusing existing browser or terminal tooling.
For headless code, mark visual work not applicable. Preserve a working shell.nix
or flake; do not migrate or add infrastructure merely to match an example.

Options are ordinary request inputs: mode bootstrap/improve/audit, language auto,
and an optional scope such as docs,env,tests,visual,ci,release. Audit is read-only;
setup and improvement perform the requested changes and verify them using the
project's own commands. Make and a release strategy remain required. Tool and
workflow selection follows project needs, not the optional checker's coverage.

Start with [SKILL.md](skills/codebase-foundation/SKILL.md), then read the relevant
[setup playbook](skills/codebase-foundation/references/project-setup.md) or
[visual workflow](skills/codebase-foundation/references/visual-workflow.md).

The bundled Rust CLI and executable verifier are **optional supporting examples**
of Make/release behavior. They neither define the skill nor validate every Go or
Python workflow. No automatic checker replaces native tests, live behavior and
visual inspection. To exercise the example implementation itself:

```sh
nix-shell
make verify-foundation
make foundation-controls
```

SDD's root workflow remains make help/setup/check/build, with separate live
monitoring targets. make release-check includes all capability checks and requires
an authorized Docker daemon. make release only prepares local files; publication,
commits, tags, pushes and deployments require explicit authorization. See
[release instructions](RELEASE.md), [repository research](docs/codebase-foundation-research.md),
[external audits](docs/codebase-foundation-audits.md), and the
[implementation report](docs/codebase-foundation-report.md) for example evidence
and its limits. Runtime results there cover the example implementation, not an
assessment of every foundation topic in this playbook.

## Interview practice: FRAME and CODE

[FRAME](skills/frame-system-design/SKILL.md) structures a system-design discussion:
frame the problem, requirements/constraints, architecture, modes of failure and
evolution. Decisions follow assumption → choice → trade-off → validation.

[CODE](skills/code-live-coding/SKILL.md) structures a live Python exercise with AI:
comprehend, outline, develop incrementally and evaluate tests plus real behavior.
It includes the supplied Claude Code exploration prompt, observability reminders
and the Neovim/Python/uv/Claude Code setup checklist. Both default to 60 minutes
and can be loaded by any compatible agent. These are based on the supplied ICEYE
preparation notes, not official company assessment criteria.

> Use frame-system-design to rehearse a 60-minute interview. Ask me to clarify
> requirements, then introduce one changed constraint after I explain a baseline.

> Use code-live-coding to review my plan for this Python exercise. Start with
> read-only inspection, then help me scope a small implementation and show how
> I will verify tests and observable behavior.

No code runs when either skill is loaded. Read-only inspection does not authorize
Make, project hooks, model CLI execution, image pulls or service startup.

## Load a skill

The portable unit is one complete directory under `skills/`, beginning
with SKILL.md. Copy or symlink that directory into your compatible agent's
configured skill search path; installation paths differ between clients. No
repository-specific agent config is necessary. An agent that can read files can
also load SKILL.md explicitly from this checkout and follow its relative links.
No plugin manifest or provider integration is required. Normal agentskills
installers can distribute this layout when the repository is published.

> Add a Prometheus and Grafana monitoring stack to this application using the
> `monitoring-stack` skill. Preserve the existing architecture, instrument
> request latency and failures, and verify that Prometheus collects the metrics.

The skill accepts ordinary task options; omitted values are resolved by inspecting
the application. For example, include this in the request:

```yaml
language: auto
metrics: prometheus
dashboards: grafana
deployment: compose
scope: full
```

You can also request “instrumentation only, keep our existing collector, no
Grafana.” This changes the adaptation scope; it does not install another stack.
[Options and coverage](skills/monitoring-stack/references/options.md) explain
resolution and tested configurations. Other backends/languages require suitable
implementations and executable checks; selecting them does not make the supplied
Prometheus/Grafana verifier generic.

Load SKILL.md first, then only the applicable adapter/contract/implementation
resources. Do not dump the whole baseline into context. Inspect existing
monitoring first and extend it; do not duplicate a registry or stack. Adapt the
reference to the application, not the application to the reference.

The [before/after Flask example](docs/adaptation.md) preserves a factory,
Blueprint and domain layer while reusing the metric helper and provisioning.
[The contract](skills/monitoring-stack/references/contract.md) defines observable
success. The baseline and demo passed real Prometheus/Grafana checks; see the
[implementation report](docs/implementation-report.md) for evidence and limits.

## Evaluate the idea

[Evaluation protocol](evaluation/README.md) prepares clean A/B workspaces and
scores completed monitoring implementations with the same external verifier and original
tests. It does not invoke agents or integrate any provider. Agent time, tokens
and tool calls remain unmeasured until actual paired runs are performed.
Feasibility is demonstrated; a performance improvement is not established.

## Add another capability

Create an ordinary skill directory with name/description frontmatter. Include
only guidance that changes engineering decisions. Supply the smallest working
reference, explicit observable contract, selective adaptation guidance and an
independent checker that can reject broken implementations. Test it in a
structurally different application and retain honest evidence. Optional resource
directory names are not a new schema; use what the capability actually needs.

## Scope

This prototype supports disposable local monitoring deployments, single-process
Python HTTP services, local SQLite-backed background jobs and a general project-foundation playbook with an optional tested Rust example. It has no package registry, dependency resolver, agent
orchestration, proprietary integration, Kubernetes, tracing, alert manager or
production deployment controller. Go/Rust monitoring and worker adapters, production worker models,
streaming request semantics and broad framework support remain future work.
