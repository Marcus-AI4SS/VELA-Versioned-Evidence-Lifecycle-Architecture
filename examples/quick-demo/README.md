# 3-Minute Quick Demo



This demo shows the smallest useful story behind VELA.



The question it answers is:



**What happens after a researcher gives Codex a real project-shaped task?**



## The Scenario



A researcher wants to start a computational social science project:



- topic: public reactions to AI-generated content labels

- materials: platform posts, comments, and academic literature

- expected outputs: a small evidence map, a coding plan, and a reproducibility-ready project folder



This is not just one answer. It has literature, platform evidence, analysis, writing, and review risk. So the stack should not immediately produce a polished essay. It should first explain the route.



## The Demo Flow



1. The user gives a project prompt.

2. The VELA route layer explains the work before execution.

3. The project coordination layer turns the route into explicit project roles.

4. A reviewer gate checks whether the output can move forward.

5. The project state files show where the work stands.



## Files To Read In Order



1. [`demo-prompt.md`](./demo-prompt.md)

2. [`route-explanation-card.md`](./route-explanation-card.md)

3. [`research-map.md`](./research-map.md)

4. [`.codex/dispatch/demo-run.yaml`](./.codex/dispatch/demo-run.yaml)

5. [`logs/project-state/current.json`](./logs/project-state/current.json)

6. [`outputs/agent-runs/demo-run/reviewer/gate.literature-producer.json`](./outputs/agent-runs/demo-run/reviewer/gate.literature-producer.json)



## What To Notice



- The route is explained before execution.

- The agent roles are explicit.

- The reviewer is linked to a specific producer.

- The project state is written to files instead of staying hidden in chat.

- The demo intentionally stops at the planning/review boundary; it does not pretend to have completed the full research project.
