# VELA Runtime Rule Sync: 2026-05-31

This log records public VELA runtime updates for the installable Codex research workflow package.

## Scope

VELA remains a portable Codex research workflow environment. This sync strengthens runtime rules, validators, route contracts, project folder hygiene, memory governance, MCP/profile policy, figure workflow, CNKI/Zotero workflow, and external adoption readiness checks.

Excluded by design:

- desktop app development workflows
- private persona or custom role payloads
- browser login state, cookies, credentials, local databases, caches, and generated private artifacts
- platform-specific social MCP backends that should not ship in the public package

## Key Updates

- Added engineering-cybernetics control contracts as the public control kernel.
- Aligned the seven-layer environment contract with VELA runtime language.
- Updated memory-system contracts so durable rules pass through explicit admission, validation, and git-backed promotion.
- Switched browser and desktop interaction policy to native-first:
  - in-app Browser for ordinary/local web targets
  - official Chrome plugin for logged-in Chrome profile, extensions, tabs, cookies, and browser downloads
  - Computer Use for Windows desktop/file-dialog work
  - MCP/CLI browser tools only as fallback or specialized automation
- Removed the retired Zotero MCP adapter as a runtime dependency; Zotero integration is through the official Zotero plugin and project-local import plans.
- Kept CodeGraph as an optional on-demand context adapter. External memory services are watch-only patterns, not runtime dependencies.
- Added project folder hygiene, local memory system, external adoption readiness, figure style presets, scientific figure workflow, CNKI/Zotero workflow, and public runtime validators.

## Runtime Structure

VELA supports a source/runtime split:

- source package: the cloned VELA repository, catalogs, schemas, scripts, docs, and tests
- runtime home: the installed Codex-facing runtime under the user's `CODEX_HOME` / `VELA_HOME`

The split is portable across Windows and macOS. Windows users use `install.ps1`; macOS/Linux users use `install.sh`. Native tool checks differ by OS, but the installed VELA contract is the same.

## Public Package Boundary

VELA is intentionally focused on public research workflow use. It does not include:

- desktop app source, release, debugging, or Tauri-specific workflows
- private persona or custom role payloads
- browser session state or paid-platform credentials
- local Obsidian/Zotero databases
- generated private outputs

External systems are classified before adoption:

- installed/required: only the VELA public runtime and its Python dependencies
- optional/on-demand: CodeGraph, specialized MCP servers, and external repository patterns
- watch-only/rejected patterns: external memory services that would add startup hooks, full transcript ingestion, or automatic prompt injection
- rejected/private: platform-specific social MCP backends and anything requiring user credentials, private caches, or non-public artifacts

## Verification

Validated on 2026-05-31:

```text
python -m unittest discover -s runtime\skills\tests
python -m unittest discover -s tests
python -m skills.scripts.envctl validate cybernetics --summary
python -m skills.scripts.envctl validate governance --summary
python -m skills.scripts.envctl validate memory --summary
python -m skills.scripts.envctl validate environment-layers --summary
python -m skills.scripts.envctl validate project-folder-contract --summary
python -m skills.scripts.envctl validate adoption-readiness --summary
python -m skills.scripts.envctl validate stack --summary
```

All tests and required validators pass. `adoption-readiness` may report warnings for optional external runtimes that are not installed; these warnings are expected and do not block VELA installation.
