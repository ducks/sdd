# Screenshot and visual verification workflow

Use for browser UIs, desktop UIs and TUIs. For a headless project mark visual
checks NOT APPLICABLE with a reason. Do not add a browser just to make a CLI's
foundation look more complete.

## Follow the existing capture mechanism

Inspect current screenshots, fixtures, browser/TUI tests, artifact paths and
update commands. Jake's existing examples use Playwright to capture BeanLedger's
dark, light and mobile views, and tuishot-generated Claux TUI snapshots under
docs/screens/. These are examples of different mechanisms, not a requirement
that every project install either one. Prefer the mechanism already in use.

For a new web UI, a small browser capture/test workflow may be appropriate.
For a TUI, use a suitable deterministic terminal snapshot/capture tool. Declare
capture tools in the development environment, document the real command through
Make or existing scripts, and keep local and CI settings aligned. Do not invent
a screenshot target that has no working capture implementation.

Use the [seed-data guidance](data-and-benchmarks.md) for reproducible demo and
screenshot states, keeping private/production data out of captures.

## Capture → inspect → change → recapture

1. Run the actual interface with synthetic data and a known configuration.
2. Capture the affected screen before editing when an existing state is useful.
   Fix viewport or terminal dimensions, theme, fonts and relevant data. Control
   clocks, animations and nondeterministic content where practical.
3. Inspect the rendered image. Check hierarchy, spacing, clipping, contrast,
   responsive layout and relevant loading/empty/error/focus states. Do not claim
   visual review from successful capture or an image filename alone.
4. Apply the smallest justified change; recapture under the same conditions and
   compare. Exercise the affected interaction as well as its appearance.
5. Review visual differences before accepting updated snapshots. A blanket
   snapshot regeneration can conceal regressions. Keep expected changes distinct
   from unrelated drift such as timestamps, versions or font differences.

For browser interfaces, include relevant desktop/mobile sizes and themes rather
than every possible combination. For a TUI, choose representative dimensions
and states. Screenshot tests complement assertions about navigation, data and
behavior; they do not replace them. Capturing dark/light/mobile images alone
does not establish that automated pixel comparison exists.

## Artifacts, CI and documentation

Keep a small set of useful, sanitized product screenshots in the documented
location when appropriate. Send transient captures/diffs to an ignored artifact
directory or CI failure artifacts. Never capture credentials, private customer
data or a developer's unrelated desktop. State whether a capture is a screenshot
of the running product, a snapshot rendering or a mockup.

Document startup, fixture setup, capture, comparison and intentional snapshot
update commands. Discover the actual commands rather than assuming a particular
runner's CLI. In Claux, TUISHOT_UPDATE=1 accepts snapshot drift and therefore
requires review; that switch has no meaning in an unrelated application.
Add visual CI checks only when they are repeatable and meaningful. Retain enough
failure evidence to diagnose a regression and clean up only owned test resources.

Report which screens/states were inspected and what remains unverified. A missing
browser/display/font is a verification limitation, not a passing screenshot check.
