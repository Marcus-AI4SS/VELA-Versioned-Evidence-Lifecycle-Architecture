# Quality Checks



VELA quality checks are plain questions a researcher can answer before sharing a claim, handoff, or deliverable.



## Before Treating A Claim As Supported



- Is the research question clear?

- Does the claim have linked evidence?

- Does the evidence actually support the claim as written?

- Are source, access time, verification status, and rights or ethics notes present?

- Are method assumptions visible?



## Before Sending A Codex Handoff



- Is the task narrow enough?

- Are relevant files named?

- Are constraints explicit?

- Is the expected output clear?

- Are known gaps listed?

- Does `vela handoff lint handoffs/Hxxx.yaml` pass?



## Before Sharing A Deliverable



- Are unsupported claims labeled as unsupported?

- Are private materials excluded?

- Is the evidence path inspectable by another person?

- Does `vela privacy scan .` report no errors?
