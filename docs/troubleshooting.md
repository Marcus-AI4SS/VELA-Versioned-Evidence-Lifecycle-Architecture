# Troubleshooting

## HELM is not installed

VELA should still be usable. HELM is an optional local board, not a requirement for the workflow environment.

## Python is not installed

The base workflow can still record materials, evidence fields, claims, method notes, deliverables, and handoff context. Python is only needed for richer checks or data-processing tasks.

## A project has blockers

Blockers mean the project record is not ready for the next claim, handoff, or deliverable. They should name the missing field or unsupported relation.

## A handoff is too broad

Rewrite the handoff so it states the task, relevant files, constraints, expected output, and known gaps. Codex should not receive the whole project when a bounded context is enough.

## Text appears garbled

Source files, project JSON, and generated readable files should be UTF-8. Avoid tools that save shared project files as ANSI or outdated encodings.
