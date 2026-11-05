# Paired evaluation protocol

This is a manual agent experiment with runnable workspace preparation and an
independent scoring harness. No model integration is implemented. The adaptation
demo is feasibility evidence, not an A/B experiment or evidence of superiority.

```sh
python3 evaluation/prepare.py /tmp/sdd-pair-001
# Separately run the same agent in A/ and B/, using requirement.txt.
# B additionally loads skills/monitoring-stack/SKILL.md.
python3 evaluation/score.py --app /tmp/sdd-pair-001/A/app --output runs/A.json --allow-exec
python3 evaluation/score.py --app /tmp/sdd-pair-001/B/app --output runs/B.json --allow-exec
```

Use fresh independent agent sessions, same model snapshot, tools, permissions,
30-minute limit, Docker cache, machine resources and initial application. A gets
no skill directory, repository access or previous B transcript. A's environment
must not expose this source repository (a filesystem copy alone is not isolation).
The requirement and engineering acceptance constraints are identical. B receives
only the additional skill availability note. Both may use the same official
library docs. Authorize reviewed fixture/container execution equally in both.
Randomize run order; use multiple pairs before estimating any effect.

The scorer copies each completed implementation to a temporary workspace and
restores the original behavior tests and acceptance mapping from outside agent
control. It runs the same 19-check verifier and cleans up. This protects the
oracle from accidental edits, not from adversarial code with Docker privileges;
use an appropriately isolated runner for untrusted submissions.

Collect these per arm from actual agent/runner logs, never estimates:

| Measure | Evidence |
| --- | --- |
| Functional correctness | Per-check JSON, all 19 checks; UNKNOWN/SKIP are not successes |
| Existing functionality | Four restored original application tests |
| Time | Monotonic start to final artifact or timeout, including verification |
| Tool calls | Agent transcript/tool-event count |
| Token consumption | Actual reported input/output/cache token counters, or UNKNOWN |
| Manual interventions | Dated log of every correction, approval and human edit |
| Quality | Blind review of architecture preservation, duplicate infrastructure, cardinality, secrets, minimal changes and maintainability |

Store raw reports, transcript references, source commits/hashes, model identifier,
settings and manual event logs alongside experiment.json. The null metrics in
that file mean unmeasured, not zero. Keep correctness separate from speed/cost;
a fast incomplete integration does not win. A single pair is illustrative only.

Preparation and scoring were smoke-tested during prototype implementation;
no independent A/B agent runs have been performed. The author had already seen
the skill and cannot serve as a blind conventional arm in the same session.
