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
On the current Windows setup, no native `computer_use` namespace is exposed to this session.
The visible browser tools are still MCP-backed, chiefly `chrome-devtools` and `social-platform-mcp`.

Treat this as a future enhancement layer for this stack until it is actually available and stable on Windows.
Do not remove `social-platform-mcp`, `chrome-devtools`, or `agent-browser` just because the Codex changelog mentions computer use.

### `social-platform-mcp`

Use when:

- the task should be expressed as a generic cross-platform capture interface
- the same evidence workflow should work across Xiaohongshu, Douyin, Bilibili, and WeChat article pages
- the capture should leave a standard artifact bundle on disk
- repeatable execution matters more than one-off manual inspection

Do not force it onto:

- one-off visible reading that `chrome-devtools` can already handle cleanly
- platform-specific public metadata queries that `xiaohongshu-mcp` already exposes better
- debugging tasks where direct `agent-browser` access is more transparent

This is the generic capture facade. It wraps the local browser-evidence workflow rather than replacing it with hidden scraping.

### `xiaohongshu-mcp`

Use when:

- Xiaohongshu search
- public note discovery
- public profile or feed metadata
- structured public note reads that the server already exposes cleanly

Do not force it onto:

- cross-platform generic capture
- browser-exact favorites pages
- board pages
- lazy-loaded collection pages
- login-gated visible-state tasks

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
In routine use it should usually sit behind `social-platform-mcp`, not become the first user-facing backend.

## Practical Rule

- native computer use available in this session -> use it for direct UI actions, then preserve the same evidence boundary
- Windows current setup -> keep `social-platform-mcp` as the stable repeatable capture layer
- one-off visible reading -> `chrome-devtools` when healthy
- repeatable cross-platform capture -> `social-platform-mcp`
- public structured Xiaohongshu metadata -> `xiaohongshu-mcp`
- debug or custom browser automation -> `agent-browser`
