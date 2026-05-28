# Skills Layer

VELA has two skill layers:

- public VELA wrapper skills in `skills/`;
- the near 1:1 local research environment distribution installed from `research-stack/local-environment/`.

Both support file contracts and bounded Codex work. CLI validators remain the final check.

Core VELA wrapper skills:

- `vela-material-intake`
- `vela-evidence-promote`
- `vela-claim-linker`
- `vela-handoff-builder`
- `vela-deliverable-review`

These skills do not require HELM, private MCP routing, Zotero, Obsidian, or a desktop app.

The local research environment distribution additionally installs research-autopilot, literature, citation, writing, figure, presentation, quantitative, review, reference-acquisition, social-platform, and submission skills. It deliberately excludes desktop app development and distilled-scholar chains, and it ships only sanitized contracts, profiles, validators, and toolchain metadata.

Use skills to help Codex follow the VELA workflow. Use `vela validate`, `vela privacy scan`, and `envctl validate ...` to decide whether a project state or environment state is acceptable.
