# Codex Wrapper Contract



VELA is a portable workflow wrapper around Codex. It does not replace Codex, run a hidden agent loop, or store private memory. It gives a research project a file-based operating layer that Codex can read, act within, and leave auditable results behind.



## Product Center



The center of VELA is the Codex handoff packet plus the files that make the handoff reviewable:



- `AGENTS.md` defines the project research contract.

- `.codex/commands/` keeps repeatable prompt patterns close to the project.

- `handoffs/` stores bounded tasks for Codex.

- `materials/`, `evidence/`, `claims/`, `methods/`, and `deliverables/` keep research objects separate.

- `logs/quality-gates/` and `logs/project-state/` keep project status inspectable.

- `.vela/context.json` exposes the current state to HELM and other readers.



## Default Loop



```text

initialize project -> create handoff -> lint handoff -> give prompt to Codex -> validate result -> record human review

```



VELA defaults to rendering prompts and validation reports. It should not silently execute Codex tasks unless the user explicitly chooses an execution bridge later.



## Layers



| Layer | VELA responsibility |

| --- | --- |

| Project scaffold | Create the folder and file shape from `package/.vela/initializer-manifest.json` |

| Codex instruction | Provide concise `AGENTS.md` and command templates |

| Handoff | Turn a task into a small, named, reviewable contract |

| Validation | Check structure, handoff schemas, context freshness, and quality gates |

| Audit | Preserve logs, quality reports, prompts, and human-review records |

| HELM interface | Write `.vela/context.json` for read-only dashboard import |



## Deferred Capabilities



VELA keeps broader governance and harness ideas behind explicit public contracts. New capabilities enter only when they strengthen the installable workflow package.



Deferred for later releases:



- dedicated evidence, claim, and deliverable validators;

- optional Codex execution bridge after prompt rendering and validation are stable.



This boundary keeps VELA usable as an installable workflow package rather than a private research automation platform.



## Machine Contracts



Current runtime validators emit `vela.validation.report.v1`. Handoff packets are parsed as JSON or YAML and checked against `vela.codex.handoff.v1`; project state is checked against `vela.project.context.v1`; initializer manifests are checked against `vela.project.initializer.v1` plus Python path-safety rules.
