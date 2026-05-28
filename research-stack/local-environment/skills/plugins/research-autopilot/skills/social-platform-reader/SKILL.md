---
name: social-platform-reader
description: Use when Codex needs to inspect Xiaohongshu, Douyin, Bilibili, WeChat public-article pages, boards, favorites, collections, notes, posts, videos, or similar platform artifacts, and must extract only directly visible evidence from a logged-in browser or a stronger installed backend.
---

# Social Platform Reader

Use this skill to read social-platform content through the strongest available backend while preserving evidence quality.
Prefer installed upstream MCPs over custom parsing when an upstream backend is mature enough for the target platform and task.
For research reporting tasks, keep extraction structured enough that the result can be handed to `research-docx-export` without another manual cleanup pass.

## Backend Order

Choose the backend in this order:

1. Use native Codex computer-use/browser capability only when it is actually exposed in the current session. As of the current Windows setup, no native `computer_use` tool is available, so do not assume it exists.
2. Use `chrome-devtools` for login-gated or browser-exact tasks when the MCP connection is healthy, especially boards, favorites, collections, user-visible tabs, lazy-loaded pages, WeChat article pages behind verification, or any case where the user asks to read what is currently visible in Chrome.
3. Add `social-platform-mcp` when the task should be turned into a standardized cross-platform capture flow with saved artifacts, repeatable execution, or a reusable evidence bundle. On Windows this is currently the most stable browser-evidence backend in this stack.
4. Use `xiaohongshu-mcp` only for Xiaohongshu tasks that match its structured platform-specific capabilities, such as search, feed detail, profile, or other public content endpoints that the server already exposes.
5. Add direct `agent-browser` only when the task is template development, capture debugging, nonstandard interaction, or another case that should bypass the generic facade on purpose.
6. Fall back to browser reading for Douyin, Bilibili, and WeChat article pages by default. Do not invent a dedicated backend unless one is already installed and clearly stronger than browser extraction for the exact task.

Read [references/upstream-backends.md](references/upstream-backends.md) when the task requires backend-selection rationale or platform extension.
Read [references/agent-browser-templates.md](references/agent-browser-templates.md) when the task should switch from one-off reading to reusable browser automation.

## Platform Routing

### Xiaohongshu

Prefer `xiaohongshu-mcp` when the task is:

- search and note discovery
- reading a note detail page that is already public and structured
- reading a profile or basic feed metadata

Prefer `chrome-devtools` when the task is:

- board, collection, or favorites pages
- login-gated state
- exact visible page extraction
- pages that require scrolling or clicking to reveal note cards
- cases where the user asks for evidence tied to what is open in their current browser

Add `social-platform-mcp` when the task is:

- board or collection traversal across multiple visible cards
- repeatable multi-step capture that should land in a standard output directory
- reusable evidence packaging across Xiaohongshu, Douyin, Bilibili, and WeChat article pages

Add direct `agent-browser` when the task is:

- template debugging or backend debugging
- repeated open -> wait -> snapshot -> screenshot loops
- saving a reusable session state for future capture runs
- producing nonstandard capture artifacts under the local research environment that the generic facade does not already cover

For Xiaohongshu boards and collections, prefer the board-scoped card URL when opening a note detail page from the browser session.
The useful pattern is `/board/<board_id>/<note_id>?xsec_token=...`, not the hidden `/explore/<note_id>` link that may appear in the DOM and can fail outside the current board context.

### Douyin

Use `chrome-devtools` by default.
Add `social-platform-mcp` when video-page capture should be standardized, repeatable, or saved as a reusable evidence package.
Add direct `agent-browser` when video-page capture needs backend debugging, custom scripts, or interaction logic that the generic facade does not yet cover.
Treat captions, author names, timestamps, and visible engagement counters as browser-observed fields. Do not infer transcript text unless the page visibly renders it or the media is explicitly transcribed in-page.

### Bilibili

Use `chrome-devtools` by default.
Add `social-platform-mcp` when a stable repeatable capture flow is more important than one-off manual inspection.
Add direct `agent-browser` only for debug or nonstandard interaction.
Read video title, uploader, publish time, description, tags, and visibly rendered transcript or summary only when those fields are on the page.

### WeChat Public Articles

Use `chrome-devtools` by default.
Add `social-platform-mcp` when the article should be captured as a repeatable browser workflow with screenshots and structured artifacts.
Add direct `agent-browser` only for debug or nonstandard interaction.
Treat title, public account name, publish date, body paragraphs, subheadings, and source link as browser-observed fields only when they are visibly rendered on the page.
If the page shows an environment exception, verification prompt, or anti-bot interstitial, stop and report the blocker rather than summarizing the article from guesses or secondary mirrors.

## Workflow

### 1. Identify the Artifact

Classify the user target before extraction:

- platform: Xiaohongshu / Douyin / Bilibili / WeChat article / other
- artifact type: board, collection, favorites, profile, search result, note, post, video, public article
- access mode: public URL, logged-in browser page, or already-open tab

If the target is ambiguous, resolve the page first and only then extract.

### 2. Choose the Backend

Use the routing rules above.
If `xiaohongshu-mcp` is unavailable or unhealthy, fall back to `chrome-devtools` when the browser can still expose the page directly.
If the task requires repeatable browser automation, prefer `social-platform-mcp` first, and switch to direct `agent-browser` only when the generic facade is insufficient.
If all applicable backends are unavailable, stop and report the missing prerequisite instead of improvising.

### 3. Use agent-browser Templates When Needed

When `social-platform-mcp` or direct `agent-browser` is selected, prefer the reusable template script over ad hoc commands:

- [scripts/run-social-platform-agent-browser-template.ps1](scripts/run-social-platform-agent-browser-template.ps1)

Default template behavior:

1. open the target URL with platform-safe defaults
2. wait for page hydration
3. collect title and final URL
4. save an interactive snapshot JSON
5. save a visible screenshot
6. optionally save session state
7. write a metadata JSON artifact

Do not treat the template output as hidden truth.
It is still only a browser-observed artifact bundle.
The difference is only orchestration:

- `social-platform-mcp` = standard MCP facade over the template chain
- direct `agent-browser` = debug or custom automation mode

### 4. Extract Only Direct Evidence

For every item, extract only fields that are directly exposed by the chosen backend or the rendered page:

- title
- author
- published_at
- body_or_caption
- tags_or_topics
- media_type
- source_link

If a field is absent, write `NOT_DISPLAYED`.
Do not infer hidden posts from counters, collection totals, or partial metadata.

### 5. Normalize the Output

Use the schema in [references/output-schema.md](references/output-schema.md).
Default output has two layers:

1. A summary table:
   `index | platform | title | author | time | 100-200 char summary | link`
2. A per-item evidence block:
   `key points + evidence fields + short explanation`

When the user asks for comment analysis, add:

3. A ranked visible-comment block:
   `comment rank | note title | author | like count | content | scope note`

If the user explicitly wants Chinese headings, translate only the final output labels, not the extracted evidence.

### 6. Handle Dynamic Pages Carefully

When the page is lazy-loaded or client-rendered:

1. snapshot the current page
2. inspect visible DOM and runtime state
3. inspect relevant network requests when needed
4. ask the user to keep the page open or scroll only if new items must be rendered

If the same interaction must be repeated across many visible items, promote the task to `social-platform-mcp` first, and only drop to direct `agent-browser` when the generic facade no longer covers the interaction cleanly.

### Xiaohongshu Board Detail Rule

When extracting note details from a Xiaohongshu board or collection:

1. collect the visible board card URL from the card footer or cover link
2. use that board-scoped URL to open the note detail page in the browser context
3. scroll the note detail page until the comment section is rendered
4. extract only currently visible top-level comments unless the user explicitly asks for deeper expansion

Do not treat a hidden `/explore/` anchor inside the card DOM as the preferred detail URL when the board-scoped URL is available.
Do not claim that missing cards or posts exist unless a direct page artifact exposes them.

## Report Handoff

If the user wants a deliverable file rather than only a chat summary:

1. keep the extraction structured
2. state the visible-evidence boundary
3. rank comments only from rendered visible comments
4. hand the structured result to `research-docx-export`

If `agent-browser` was used, keep the artifact directory path in the report notes so the screenshots and snapshot JSON can be audited later.
If `social-platform-mcp` was used, keep the same artifact directory path because the facade is only a standardized wrapper around the same browser-evidence workflow.

## Failure Rules

Stop and explain the blocker when:

- the required MCP server is unavailable
- Chrome remote debugging is not enabled when `chrome-devtools` is required
- the user is not logged in for a login-gated page
- the page structure changed and no direct evidence can be recovered
- the platform blocks rendering or the backend returns incomplete data
- a WeChat article requires verification or shows an environment exception page

When blocked, report four things:

1. what page or tool was checked
2. what direct evidence was found
3. why the evidence is insufficient
4. the smallest next action required from the user

When comments are requested, also report whether the result covers:

- only visible top-level comments
- visible replies that were explicitly expanded
- or the full rendered comment set after scrolling

## Scripts

Use these scripts instead of rewriting setup steps by hand:

- [scripts/run-social-platform-agent-browser-template.ps1](scripts/run-social-platform-agent-browser-template.ps1): reusable `agent-browser` capture template for Xiaohongshu, Douyin, Bilibili, and WeChat article pages

## References

- Use [references/upstream-backends.md](references/upstream-backends.md) for backend selection rationale.
- Use [references/output-schema.md](references/output-schema.md) for the normalized extraction format.
- Use [references/agent-browser-templates.md](references/agent-browser-templates.md) for template selection and command examples.
