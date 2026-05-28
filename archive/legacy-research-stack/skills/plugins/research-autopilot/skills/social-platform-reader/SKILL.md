---
name: social-platform-reader
description: Use when the task needs browser-visible evidence from Douyin, Bilibili, WeChat public articles, or similar social-platform artifacts.
---

# Social Platform Reader

Use this skill when research work depends on visible social-platform evidence.

## Backend Order

1. `chrome-devtools` for exact browser-visible reading
2. `social-platform-mcp` for repeatable cross-platform capture
3. direct `agent-browser` only for debugging or custom automation

## Evidence Rule

Extract only directly observable fields:

- title
- author
- visible time or published date
- body or caption
- tags
- media type
- source link

If a field is not rendered, mark it as missing instead of inferring it.

## Reporting Rule

Keep output structured enough for later export:

1. summary table
2. item-level evidence blocks
3. optional ranked visible-comment section

## References

- `references/upstream-backends.md`
- `references/agent-browser-templates.md`
- `references/output-schema.md`
