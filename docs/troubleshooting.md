# Troubleshooting

## Python is not installed

The base workflow can still record materials, evidence fields, claims, method notes, deliverables, and handoff context. Python is needed for the CLI, richer checks, validators, and data-processing tasks.

## A project has blockers

Blockers mean the project record is not ready for the next claim, handoff, or deliverable. They should name the missing field or unsupported relation.

## A handoff is too broad

Rewrite the handoff so it states the task, relevant files, constraints, expected output, and known gaps. Codex should not receive the whole project when a bounded context is enough.

## A tool is missing

Run `vela doctor`. Missing optional tools should be reported as missing or optional, not as installed. Install only the tools needed for the current workflow.

## Text appears garbled

Source files, project JSON, and generated readable files should be UTF-8. Avoid tools that save shared project files as ANSI or outdated encodings.
