# Contributing



## What We Welcome



- clearer docs for research users

- safer contract checks

- better public examples

- cleaner plugin metadata

- stronger multi-agent orchestration ergonomics



## Contribution Rules



- keep changes explainable to a first-time GitHub visitor

- do not introduce hidden runtime assumptions

- prefer relative paths and portable defaults

- preserve the public privacy boundary

- do not weaken citation or evidence rules for convenience



## Good Pull Requests



- one focused change

- updated docs when behavior changes

- tests or validation notes when contract behavior changes

- no private machine paths, keys, or user-specific state



## Before You Open a PR



Run the public validators:



```powershell

python .\scripts\validate_research_stack.py

python .\scripts\validate_agents_contract.py

python .\scripts\validate_research_pipeline.py

```
