# Project Structure

VELA does not require a hidden database. A project should be readable as files and folders.

## Runtime Shape

```text
my-research-project/
  .codex/
  .vela/
  materials/
  evidence/
  claims/
  methods/
  deliverables/
  handoffs/
  logs/
```

`vela init` materializes this shape from `package/.vela/initializer-manifest.json`, then writes `.vela/context.json` through the VELA context contract. The initializer is schema-driven so new project files and directories can be reviewed without hunting through Python code.

## Installed Environment Shape

Every VELA user gets a source package plus a local runtime:

```text
vela/                         # cloned or downloaded source package
~/.codex/skills/              # public VELA research skills installed for Codex
~/.vela/research-stack/       # contracts, schemas, profiles, validators, envctl modules
~/.vela/bin/                  # vela/envctl shims
~/.vela/state/                # install receipts and doctor state
```

`CODEX_HOME` and `VELA_HOME` can override the runtime targets. This is the same source/runtime split used by the original local environment, but without copying private machine state.

## Repository Shape

| Path | Role |
| --- | --- |
| `package/` | Starter package copied into a user project |
| `package/.vela/initializer-manifest.json` | Schema-driven source for starter directories and files |
| `schemas/` | Machine-readable VELA/HELM contracts and initializer schemas |
| `scripts/vela.py` | CLI entrypoint |
| `scripts/vela_initializer.py` | Manifest loader, renderer, path guard, and materializer |
| `scripts/vela_contract.py` | Context, validation, and HELM-readable state contract |
| `scripts/init_research_project.py` | Thin wrapper that combines Git setup, manifest materialization, starter package install, Codex trust, and context export |
| `skills/` | Optional VELA Codex skill entrypoints |

## What To Keep Private

Keep raw private data, credentials, account traces, personal notes, and restricted source material inside your own project storage. Do not place them in a public copy of VELA.

## What HELM Reads

If you use HELM, it should read the project state you already maintain. HELM is a view over the work, not the only place where the work exists.
