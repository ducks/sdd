# Seed data and benchmarks

Use the project's existing fixture, factory, migration and benchmark tools first.
Add only enough structure to make demos, tests and useful measurements repeatable.
These are related workflows with different requirements, not one shared mutable
production-like database.

## Demo seed data

Provide synthetic, representative data for the main user workflows. Include
useful relationships and a few empty, error or boundary states rather than a
large pile of random records. Stable IDs, dates and random seeds help reproduce
demos and screenshot states. Use a controlled clock where relevant; don't depend
on today's date to keep a demo working.

Make loading explicit and documented. Use a repeatable seed/upsert operation or
recreate an owned disposable data store; explain which behavior applies. Verify
expected records and relationships, then exercise a representative application
flow. Run the seed operation twice to confirm its documented repeat behavior.
Don't invent demo credentials that could be mistaken for production credentials.
Never include real customer records, private data or secrets.

For an application that benefits from this workflow, expose commands such as
make seed and make demo through existing scripts. A reset command must identify
its local/test target and remove only owned data. Refuse an ambiguous or production
target; use explicit confirmation for destructive work outside a disposable test
fixture. Do not make ordinary setup silently erase or reseed a database.

## Test fixtures

Prefer small fixtures owned by each test or test group, with isolation and cleanup.
Use the same domain validation as real application data where practical. Cover
success, missing data, invalid inputs and relevant boundary/failure cases.
Tests should not rely on a developer having run the demo seed first or on other
tests executing in a particular order. A test suite may intentionally load a
shared immutable fixture; document that choice and isolate subsequent mutations.

Version fixture schemas/generators alongside the code. Generate large data sets
from a reproducible seed when useful instead of committing huge artifacts.
Document external fixture provenance and licensing if synthetic data cannot
serve the purpose. Align screenshot/demo fixtures where that helps visual
repeatability, without tying the entire test suite to a UI demo database.

## Benchmarks

Add benchmarks when a project has meaningful performance or evaluation questions.
Start with a representative operation and a baseline, not a leaderboard. Use
native tooling where it fits: Go benchmark functions, an existing Python benchmark
runner, an established Rust harness, or the application's current load-test tools.
Do not add a framework or paid model/service dependency merely to fill this section.

Define the workload and what correctness means before timing it. Check output or
invariants so a broken implementation cannot appear faster by doing less work.
Record workload/data version, generator seed, input size, concurrency, source
revision and dirty state, tool/dependency versions, relevant configuration and
hardware/runtime conditions. Distinguish cold start from warmed execution and
setup cost from measured work. Hold relevant conditions fixed for comparisons.

Choose metrics that answer the question: elapsed time/throughput, latency
distribution, allocations/memory, or task success and cost when applicable.
Repeat measurements and retain raw results, sample counts and a useful summary
of variation; don't claim a precise improvement from one noisy run. Account for
failures, interruptions, retries and unavailable measurements explicitly. Do not
silently drop failed runs or compare incompatible workloads as equivalent.

For model/agent evaluations, preserve model/provider/harness/settings identity,
attempt accounting and development versus held-out data separation. Record known
costs and missing cost coverage. Network/provider variation and different hardware
limit comparisons; state those limits rather than hiding them in an average.

Expose a documented make bench or existing equivalent where useful, with a small
local smoke workload and explicit larger runs. Keep resource use bounded and
require authorization for paid/external runs. Store transient output in an ignored
results directory; retain intentional, versioned baselines with provenance. Do not
overwrite a baseline automatically or convert a noisy timing threshold into an
ordinary CI gate without evidence that it is stable.

## Verification and handoff

Show the seed command and the representative behavior it enables. Prove tests
start with their own data and clean up. For benchmarks, run the documented small
workload, validate correctness, inspect actual measurements and record comparison
conditions. Missing dependencies or unexecuted measurements remain unverified.
A seed file's existence is not a working demo, and a benchmark command's successful
exit is not evidence of an improvement.
