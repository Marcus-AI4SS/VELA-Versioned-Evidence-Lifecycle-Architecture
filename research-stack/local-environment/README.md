# Local Research Environment Snapshot

This directory mirrors the current local Codex research environment for VELA.

It is a source snapshot, not an automatic runtime installer. VELA can read it to adopt local rules, workflows, validators, memory governance, tool profiles, and documentation. The existing VELA initializer remains stable unless a future change explicitly promotes part of this snapshot into the default package.

## Included

- engineering-cybernetics control kernel and source-rule contracts
- seven-layer environment governance: execution, tool, context, lifecycle, observability, verification, governance
- local memory system contracts and validators
- research routing, project initializer, team planning, and clarification contracts
- literature acquisition, CNKI/Google Scholar/Zotero evidence paths, citation evidence rules
- structured reading, manuscript writing, peer review, revision, figure, presentation, submission, and empirical quantitative workflows
- MCP/profile configuration templates and toolchain inventory
- envctl modules, validators, scripts, schemas, tests, and product overview assets

## Excluded

- desktop app development skills and profiles
- distilled scholar generation, scholar panel, and personal scholar-role material
- runtime caches, generated outputs, browser state, cookies, credentials, and personal secrets
- machine-specific absolute paths; `skills/catalog/settings.toml` is converted to placeholders

## How VELA Should Use It

1. Read `manifest.json` first.
2. Treat `skills/catalog` and `skills/schemas` as the contract layer.
3. Treat `skills/plugins/research-autopilot/skills` as the skill source layer.
4. Treat `skills/profiles` as MCP/profile intent, not as user config to write blindly.
5. Promote changes into VELA only through explicit schema, tests, and privacy review.

