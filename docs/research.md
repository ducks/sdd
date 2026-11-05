# Research and design decisions

Reviewed 2026-11-04, before implementation. This is a focused comparison, not
an exhaustive novelty claim. SDD here means Skill-Driven Development; Spec Kit
uses the same acronym for Spec-Driven Development.

| Existing approach | What it already supplies | Reuse / boundary |
| --- | --- | --- |
| [Agent Skills specification](https://agentskills.io/specification) and [Anthropic skills](https://github.com/anthropics/skills) | SKILL.md frontmatter, progressive disclosure, optional executable helpers, references and assets. Anthropic's webapp-testing skill already packages lifecycle helpers and executable browser tests. | Use the format unchanged. Executable skills are not a new invention. |
| [Grafana skills](https://github.com/grafana/skills) | PromQL, dashboarding, instrumentation and provisioning guidance. PromQL guidance checks real queries; dashboard guidance reads back created dashboards. Repository CI also checks skill/package structure. | Reuse their operational practices, not their marketplace/plugin structure. Structural skill validation alone does not demonstrate a deployed monitoring integration. |
| [Spec Kit](https://github.com/github/spec-kit) | Specifications, reusable process templates, quality gates and documented verification. | Adopt explicit acceptance contracts; do not create another agent workflow runtime. |
| [Backstage templates](https://backstage.io/docs/features/software-templates/writing-templates/) | Parameterized templates and actions, including custom integration actions. [Dry runs](https://backstage.io/docs/features/software-templates/dry-run-testing/) simulate action effects and support tests. | A powerful existing solution when a developer portal is wanted. Avoid its service/control-plane dependency here. Dry-run rendering and live service acceptance test different properties. |
| [Cookiecutter](https://github.com/cookiecutter/cookiecutter) | Working project templates, conditional generation and [Python/shell hooks](https://cookiecutter.readthedocs.io/en/stable/advanced/hooks.html) for validation and setup. | Reusable baselines are established practice. Hooks can implement verification, but generation is not architecture-sensitive adaptation by itself. No templating engine needed for one baseline. |
| [skills.sh](https://skills.sh) | Skill discovery, installation and distribution using existing agent integrations. | Keep the directory installable as an ordinary skill; do not build a registry or installer. |

## Closest approaches and gap

The closest combination is ordinary Agent Skills with executable helpers,
Grafana's domain knowledge, and tested scaffold templates. Existing tools can
already express much of this. The hypothesis is about packaging and practice:
keep a functioning capability, selective adaptation guidance and independent
runtime acceptance together, and evaluate whether that helps an agent preserve
an existing application's architecture. This prototype claims no new standard.

## Architecture

One skill directory contains a WSGI Python baseline, a Flask adaptation reference,
monitoring configs, and a Python verifier. Docker Compose supplies only the app,
Prometheus and Grafana. The verifier talks to their real HTTP APIs, generates
traffic, compares counters across scrapes and queries Grafana's Prometheus proxy.
It reports PASS/FAIL/SKIP/UNKNOWN per check; incomplete results never exit zero.
No model calls, agent runtime, service registry or package manager is involved.

Two example trees preserve an uninstrumented Flask application and its adapted
version. The baseline remains a separate stdlib WSGI service. A manual paired
A/B protocol uses clean copies and the same independent verifier; no claim of
agent performance improvement is made without that experiment.

## Engineering references

- https://prometheus.io/docs/practices/instrumentation/
- https://prometheus.github.io/client_python/instrumenting/counter/
- https://grafana.com/docs/grafana/latest/administration/provisioning/
- https://grafana.com/docs/grafana/latest/developer-resources/api-reference/http-api/data_source/
- https://docs.docker.com/compose/how-tos/startup-order/

Prefer bounded route-template labels, seconds-based histograms, finite error
classes, local-only published ports, and live query checks. Grafana's legacy
API is version-pinned here; migrating to a newer major requires retesting.
