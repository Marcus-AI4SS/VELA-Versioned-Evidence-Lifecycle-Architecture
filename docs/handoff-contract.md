# Handoff Contract



The VELA handoff is the central object for Codex work. It turns a user request into a small, auditable task packet.



Runtime schema: `vela.codex.handoff.v1`.



Required fields:



- `schema_version`

- `handoff_id`

- `created_at`

- `scope.task`

- `scope.relevant_files`

- `constraints`

- `expected_output.format`

- `expected_output.path`

- `review_standard`

- `completion.human_review_required`



Commands:



```powershell

vela handoff new --project . --template claim-check

vela handoff lint handoffs\H001.yaml

vela handoff render handoffs\H001.yaml --out handoffs\H001.prompt.md

```



`render` fails when `lint` fails. VELA prepares the prompt; it does not silently run `codex exec`.
