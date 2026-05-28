# Upstream Backends

## Decision Rule

Choose the narrowest backend that can recover the required evidence without inventing hidden fields.

## Current Backend Stack

### `social-platform-mcp`

Use when:

- the task should be expressed as a generic cross-platform capture interface
- the same evidence workflow should work across Douyin, Bilibili, and WeChat article pages
- the capture should leave a standard artifact bundle on disk
- repeatable execution matters more than one-off manual inspection

Do not force it onto:

- one-off visible reading that `chrome-devtools` can already handle cleanly
- one-off visible reading that should stay in `chrome-devtools`
- debugging tasks where direct `agent-browser` access is more transparent

This is the generic capture facade. It wraps the local browser-evidence workflow rather than replacing it with hidden scraping.

### `chrome-devtools`

Use when:

- the user wants the exact content visible in their current Chrome
- login state matters
- a page must be read exactly as rendered
- DOM and network inspection are needed during a one-off investigation

This is still the default primary browser chain for social-platform reading.

### `agent-browser`

Use when:

- the same browser interaction must be repeated
- the task needs scripted scrolling, clicking, waiting, and artifact export
- session persistence matters
- the task benefits from reusable local capture templates
- screenshots and snapshot JSON should be stored under the research environment

This is an enhancement layer, not a replacement for `chrome-devtools`.
In routine use it should usually sit behind `social-platform-mcp`, not become the first user-facing backend.

## Practical Rule

- one-off visible reading -> `chrome-devtools`
- repeatable cross-platform capture -> `social-platform-mcp`
- debug or custom browser automation -> `agent-browser`
