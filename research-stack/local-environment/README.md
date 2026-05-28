# Local Research Environment Distribution

This directory is the sanitized near 1:1 VELA distribution of the current local Codex research environment.

It is installable through `vela local-env install-runtime --include core,automation,toolchain --commit`. The installer copies the public research skills into `CODEX_HOME/skills`, places contracts, schemas, profiles, validators, scripts, and toolchain metadata under `VELA_HOME/research-stack/local-environment`, creates an `envctl` shim under `VELA_HOME/bin`, and writes receipts for `doctor-runtime`.

The project initializer remains separate: `vela init` creates a VELA research project, while `vela local-env install-runtime` installs the broader Codex research environment and runtime shims.

## Included

- engineering-cybernetics control kernel and source-rule contracts
- seven-layer environment governance: execution, tool, context, lifecycle, observability, verification, governance
- local memory system contracts and validators
- research routing, project initializer, team planning, and clarification contracts
- literature acquisition, CNKI/Google Scholar/Zotero evidence paths, citation evidence rules
- structured reading, manuscript writing, peer review, revision, figure, presentation, submission, and empirical quantitative workflows
- MCP/profile configuration templates and toolchain inventory
- Python requirements and environment manifests without Python/JDK runtime binaries
- envctl modules, validators, scripts, schemas, tests, and product overview assets

## Excluded

- desktop app development skills and profiles
- distilled scholar generation, scholar panel, and personal scholar-role material
- vendored Python/JDK runtime binaries
- runtime caches, generated outputs, browser state, cookies, credentials, and personal secrets
- machine-specific absolute paths; `skills/catalog/settings.toml` is converted to placeholders

## How VELA Should Use It

1. Read `manifest.json` first.
2. Use `vela local-env install-runtime --include core,automation,toolchain --commit` for user installation.
3. Treat `skills/catalog` and `skills/schemas` as the contract layer.
4. Treat `skills/plugins/research-autopilot/skills` as the public skill source layer.
5. Treat `skills/profiles` as MCP/profile intent; apply profiles only through explicit `envctl apply-profile --commit`.
6. Treat `runtime/manifest.json` as the C-drive runtime bootstrap contract: C-drive runtime data is probed or installed into, never exported.
7. Promote future local changes into VELA only through schema, tests, and privacy review.

