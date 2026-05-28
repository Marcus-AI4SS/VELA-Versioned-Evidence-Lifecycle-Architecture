# VELA

**Versioned Evidence Lifecycle Architecture**

VELA is a portable Codex workflow package for evidence-based research projects. It gives each project a readable file structure, schema-checked handoffs, evidence and claim ledgers, validation reports, privacy scans, and a machine-readable project context.

Its operating model is engineering-cybernetic: objectives, state, feedback signals, validation gates, and correction loops are all visible in files.

It can interoperate with HELM through explicit local files, but VELA does not require HELM.

## Visual Guide

![Engineering cybernetics and seven layers](./assets/overview/01-engineering-cybernetics-seven-layers.png)

![Architecture](./assets/overview/02-vela-architecture.png)

![Memory and self-evolution governance](./assets/overview/03-memory-evolution-governance.png)

![Usage roadmap](./assets/overview/04-vela-usage-roadmap.png)

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
- memory and self-evolution governance where durable rules require validation, tests, and versioned commits
- optional runtime skills and `envctl` helpers installed into the user's own Codex environment
