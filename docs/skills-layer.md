# Skills Layer

VELA includes two skill surfaces:

| Surface | Purpose |
| --- | --- |
| `skills/` | Small VELA-specific entrypoints for material intake, evidence promotion, claim linking, handoff building, and deliverable review |
| `runtime/skills/` | Optional public research skills and validators installed into the user's Codex runtime |

The runtime skills are optional. A project created by `vela init` remains usable even when no runtime skills are installed.

Use validators to decide whether a project state is ready:

```bash
vela validate .
vela handoff lint handoffs/H001.yaml
vela privacy scan .
```
