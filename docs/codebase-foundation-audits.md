# Unfamiliar repository evaluations

Read-only source audits on 2026-11-11. Source archives were downloaded from
GitHub at fixed revisions, extracted with Python's data filter, and hashed.
No upstream commands, installations, tests, hooks or builds were executed.
Before/after hashes of every extracted file matched. No upstream files changed.
Both projects carry BSD-3-Clause licenses. Reports are local evaluation artifacts,
not contributions or communications to either project.

| Project | Type | Revision | Automated inventory |
|---|---|---|---|
| [Click](https://github.com/pallets/click/tree/8abb77a8432e03ed14a95f972b44f905279415a7) | CLI-building library | 8abb77a8432e03ed14a95f972b44f905279415a7 | 5 PASS, 1 FAIL, 12 SKIP, 8 UNKNOWN |
| [Healthchecks](https://github.com/healthchecks/healthchecks/tree/255075ce65ee0997fd9d3b8dd04e4829a87fad5d) | Django monitoring application with databases and notification integrations | 255075ce65ee0997fd9d3b8dd04e4829a87fad5d | 4 PASS, 1 FAIL, 12 SKIP, 9 UNKNOWN |

These counts describe checker observations, not overall quality scores. Both
FAIL findings are absence of the mandatory root Makefile, a deliberate SDD
contract requirement rather than evidence that these mature projects cannot
build or test. The following manual assessment supplements automatic inventory.

## Click

Detected pyproject metadata with version 8.6.0.dev and a development dependency
group; uv.lock, src/ layout, tests/, CHANGES.md, README and BSD license. Manual
inspection found pytest discovery configuration, warning-as-error policy,
Ruff/pre-commit, typing checks, tox with uv's locked environment runner, multi-
platform CI and a Flit build. The publishing workflow sets SOURCE_DATE_EPOCH,
builds wheel/sdist, creates a draft GitHub Release and uses a protected publishing
environment with PyPI trusted publishing. None of those commands were run.

Required SDD improvement: thin Make aliases over those existing commands and an
explicit local release-check/preview interface. Preserve tox, uv, Flit and their
existing quality gates. A pending 8.6.0 Unreleased section is not a broken release
because the source version is 8.6.0.dev. The checker cannot normalize this policy
and correctly leaves changelog readiness UNKNOWN. Do not demand Nix migration,
Docker, health endpoints, a database, the Rust helper or a second release tool.
The repository is larger than a tiny example, but remains a single CLI library
with no service dependencies and a meaningfully different development workflow.

## Healthchecks

Detected dependency files, README, changelog, license, manage.py, existing Docker
and Compose files. Manual inspection found a real application with Python 3.12+,
Django 6.1, PostgreSQL/MySQL/MariaDB support, dependency constraints, native build
prerequisites and CI across four databases/Python versions. CI runs manage.py
test; contributing docs describe Ruff and documentation rendering. The Docker
image runs as a service account and has a health check. Publication is tied to
published GitHub Releases or manual dispatch and builds three image platforms;
it is not a cargo-style binary release. Changelog includes versioned operational
migration notes, including changed process supervision in version 5.0.

Required SDD improvement: Make aliases over existing application commands, an
explicit source/image version policy and local release-readiness boundary, and
verified deployment/recovery procedures. Preserve its existing dependent-service
setup. Test database isolation, config validation, notification behavior, health
and migrations before claiming operational readiness. Docker is justified here;
adding another monitoring stack, worker framework or Nix requirement solely to
match the baseline would be unnecessary. Runtime behavior, production rollback,
publication authorization enforcement and exact deployed version identity remain
unverified. Its stated contribution policy rejects AI-generated submissions;
this evaluation makes no submission or contact.

## False positives, false negatives and adjustments

The first documentation scanner matched ordinary phrases such as “make sure”
and “make it” as command targets. Restricting to shell command examples and
inline code removed those confirmed false positives. An initial regex still
mistook closing Markdown fences for opening fences, capturing intervening prose;
a line-oriented fence parser fixed it. A regression includes multiple code
blocks separated by natural prose. Final audits report no such documentation
failure. Original provisional reports were replaced with corrected observations;
no claim is made that the original scanner was correct.

Automated inventory under-detects Click's tox/Flit release controls and
Healthchecks' custom version/deployment conventions. These are documented coverage
gaps, not failures to be fixed upstream. It does not deeply parse workflow action
implementations, prove dependency/environment reproducibility, inspect all test
assertions, or certify operational behavior. Missing Make is detected correctly;
claims that no tests/releases exist would be false. The manual review prevents
those recommendations. There is no evidence that every possible false negative
has been eliminated.

## Reproduction

Source URLs and archive SHA256 values are recorded in
[evidence/foundation/click-audit.json](evidence/foundation/click-audit.json) and
[evidence/foundation/healthchecks-audit.json](evidence/foundation/healthchecks-audit.json).
Download the codeload archive for the recorded revision, extract without running
code, then run (report outside the extraction):

```sh
python3 skills/codebase-foundation/verify/run.py --project /tmp/click-REVISION --output /tmp/click-audit.json
python3 skills/codebase-foundation/verify/run.py --project /tmp/healthchecks-REVISION --output /tmp/healthchecks-audit.json
```

Both should exit 1 for the missing mandatory Makefile; runtime checks remain
SKIP. Neither command has --allow-exec. Upstream source may later change; compare
only the recorded revisions when reproducing these observations.
