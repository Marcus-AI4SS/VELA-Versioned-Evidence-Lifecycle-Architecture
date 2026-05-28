# Integrations



VELA works without optional tools. Integrations should make the workflow easier to inspect, not make the workflow dependent on one product.



## Codex



Codex receives bounded handoffs: task, files, constraints, expected output, and known gaps.



## HELM



HELM is the optional Hub for Evidence, Logs & Monitoring. It can show status, evidence, files, logs, local checks, and Codex handoff readiness. VELA remains usable without it.



The VELA and HELM boundary is file-based. HELM imports `vela.project.context.v1`; VELA imports `helm.codex.handoff.v1`. See [VELA and HELM import interface](./imports/vela-helm-interface.md).



## Zotero And Obsidian



Zotero can manage formal references. Obsidian can hold long-lived notes. VELA should point to those tools without copying private databases into the public workflow package.



## Python Or Analysis Tools



Use Python, R, notebooks, GIS tools, or statistical software where appropriate. VELA records the state and evidence path around that work.
