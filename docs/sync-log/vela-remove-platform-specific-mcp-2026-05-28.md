# VELA platform-specific MCP removal - 2026-05-28

## Scope

Removed the excluded platform-specific social MCP backend and its public adapter references from the public VELA repository.

## Changes

- Removed the backend from public MCP profiles and social-platform routing.
- Removed it from the local-environment runtime snapshot and historical legacy archive.
- Removed the public adapter examples and dedicated scripts tied to the excluded platform backend.
- Updated social-platform reader guidance to use browser-visible evidence first, `social-platform-mcp` for repeatable capture, and `agent-browser` only for debugging or custom automation.
- Added a sync-sanitizer guard so future local-environment snapshot exports do not reintroduce the excluded platform-specific MCP token.

## Boundary

VELA still supports browser-visible platform evidence workflows. It does not ship or advertise the excluded platform-specific MCP backend or its public adapter examples.

## Verification

- `python -m unittest discover -s tests`
- `python research-stack/local-environment/skills/scripts/validate_research_stack.py`
- Repository search for the excluded MCP token returned no matches.
- Private path scan returned no matches.
- `git diff --check`
