# Upstream Backends

## Decision Rule

Choose the narrowest backend that can recover the required evidence without inventing hidden fields.

## Current Backend Stack

### Native Codex computer use / browser

Use when:

- Codex exposes a native computer-use or browser-control tool in the current session
- the task needs direct UI operation rather than a reusable evidence package
- the tool can access the target page in the same visible browser context the user intends

Do not assume it exists.
When native computer use is unavailable, the visible browser workflow should rely on `chrome-devtools` plus reusable `agent-browser` templates.

Treat this as a future enhancement layer for this stack until it is actually available and stable on Windows.
Do not assume native computer use replaces `chrome-devtools` or reusable agent-browser templates until it is available and stable.

### Reusable `agent-browser` templates

Use when:

- the task should be expressed as a generic cross-platform capture interface
- the same evidence workflow should work across Douyin, Bilibili, and WeChat article pages
- the capture should leave a standard artifact bundle on disk
- repeatable execution matters more than one-off manual inspection

Do not force it onto:

- one-off visible reading that `chrome-devtools` can already handle cleanly
- one-off visible reading that should stay in `chrome-devtools`
- debugging tasks where direct `agent-browser` access is more transparent

This is the browser-evidence template workflow. It wraps the local browser-evidence workflow rather than replacing it with hidden scraping.

### `chrome-devtools`

Use when:

- the user wants the exact content visible in their current Chrome
- login state matters
- a page must be read exactly as rendered
- DOM and network inspection are needed during a one-off investigation

This is still the default primary browser chain for social-platform reading.
On Windows it may depend on Chrome remote debugging and can fail if the browser-side connection is not available.

### `agent-browser`

Use when:

- the same browser interaction must be repeated
- the task needs scripted scrolling, clicking, waiting, and artifact export
- session persistence matters
- the task benefits from reusable local capture templates
- screenshots and snapshot JSON should be stored under the research environment

This is an enhancement layer, not a replacement for `chrome-devtools`.
In routine use it should usually sit behind reusable templates, not become the first user-facing backend.

## Practical Rule

- native computer use available in this session -> use it for direct UI actions, then preserve the same evidence boundary
- native computer use unavailable -> keep reusable `agent-browser` templates as the repeatable capture layer
- one-off visible reading -> `chrome-devtools` when healthy
- repeatable cross-platform capture -> reusable `agent-browser` templates
- debug or custom browser automation -> `agent-browser`
