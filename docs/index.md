# VELA

**Versioned Evidence Lifecycle Architecture**

VELA is a portable Codex workflow package for evidence-based research projects. It gives each project a readable file structure, schema-checked handoffs, evidence and claim ledgers, validation reports, privacy scans, and a local context file that HELM can read.

Its operating model is engineering-cybernetic: objectives, state, feedback signals, validation gates, and correction loops are all visible in files.

## Start

```bash
git clone https://github.com/Marcus-AI4SS/VELA.git vela
cd vela
sh ./install.sh --bootstrap-tools
vela init ../my-research-project --skip-codex-trust
```

Windows users can run `.\install.ps1 -BootstrapTools`. macOS users can run `sh ./install-macos.sh`.

## What VELA Adds

- a project scaffold for materials, evidence, claims, methods, deliverables, handoffs, and logs
- `AGENTS.md` rules for bounded Codex work
- `vela.codex.handoff.v1` handoff packets
- `.vela/context.json` using `vela.project.context.v1`
- validators for project structure, handoffs, privacy, and sharing readiness
- engineering-cybernetic governance for objectives, state, feedback, gates, and correction
- optional runtime skills and `envctl` helpers installed into the user's own Codex environment

## VELA + HELM

VELA is the workflow package. HELM is the optional local research board. VELA can be used alone; HELM can read VELA project state when `.vela/context.json` is present.

Read the [VELA and HELM interface](./imports/vela-helm-interface.md).
