# Architecture

VELA has three layers:

| Layer | Files |
| --- | --- |
| Project package | `package/`, copied into a research project by `vela init` |
| Runtime package | `runtime/`, installed only when the user wants VELA-managed skills and `envctl` helpers |
| Public contracts | `schemas/`, used by the CLI, documented readers, and validators |

Across those layers, VELA uses an engineering-cybernetic control loop: declare the research objective, observe project state, collect feedback, run gates, and apply bounded corrections.

## Project Layer

`vela init` creates a project with:

```text
materials/
evidence/
claims/
methods/
deliverables/
handoffs/
logs/
.codex/
.vela/context.json
AGENTS.md
```

The project layer is portable. It can be committed, zipped, reviewed, or opened by documented local readers.

## Runtime Layer

The optional runtime installs into the user's home directory:

```text
~/.vela/
~/.codex/skills/
```

It contains public skills, profiles, validators, and shims. External services remain user-managed.

## Interface Layer

VELA writes `.vela/context.json` using `vela.project.context.v1`. Readers must treat missing fields as unknown rather than success, and any write-back must be explicit and user-controlled.
