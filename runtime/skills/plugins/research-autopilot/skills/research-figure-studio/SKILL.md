---

name: research-figure-studio

description: Use when the user intends to create, redesign, polish, audit, or submit social-science research figures, paper figures, scientific illustrations, mechanism diagrams, conceptual frameworks, workflow diagrams, research-design figures, result figures, multi-panel figures, or image2-assisted academic visuals. Automatically use this skill for requests to draw figures for papers, reports, manuscripts, top-journal review, or research presentations.

---



# Research Figure Studio



This skill is the default workflow for social-science research figures and paper-ready scientific illustrations.



## Trigger



Use this skill whenever the user asks to:

- 画论文图、科研图、机制图、概念图、流程图、研究设计图、结果图、多面板图、顶刊风格图。

- improve an existing figure for manuscript review, submission, report, defense, or academic presentation.

- use image2, image generation, diagram generation, SVG, PPT, HTML, Python, R, or other tools to make a research figure.



Do not treat this as a generic poster, marketing graphic, dashboard, or app UI task.



## Required References



Before producing a serious figure, read only the relevant parts:

- `references/social-science-top-journal-figure-style.md`

- `references/image2-figure-contract.md`

- `<VELA_RUNTIME_ROOT>\skills\catalog\scientific_figure_workflow.json`

- `<VELA_RUNTIME_ROOT>\skills\catalog\publication_style_rules.json`



## Core Rule



Research figures must be argument-bearing evidence objects. They must show a claim, a mechanism, a design, a comparison, a model, a data result, or a workflow that the surrounding manuscript actually needs.



## Scientific Figure Standards



Use `scientific_figure_workflow.json` as the shared contract for figure production standards.



For conceptual, mechanism, research-design, workflow, and image2-first figures:

- Lock the exact structure, text, arrows, panel count, palette, and unsupported-claim prohibitions before rendering.

- Apply the typography contract unless the target venue requires another house style: serif fonts; Chinese fallback `SimSun`, `Songti SC`, `Source Han Serif SC`, `Noto Serif CJK SC`; English fallback `Times New Roman`, `Liberation Serif`, `DejaVu Serif`; base 10 pt; captions 9 pt; panel labels 10 pt.

- Keep figure text short enough to remain readable at single-column or double-column manuscript sizes.

- Prefer PDF/SVG/PPT/editable source for final use, with PNG preview as needed.



For empirical data panels inside a mixed figure set:

- Delegate the numeric chart/table panel to `figure-table-studio`.

- Require data health, process data, statistical justification, caption, and export records before the panel is accepted.

- Do not use image2 to generate or repair empirical numbers, p-values, sample sizes, axes, error bars, or source notes.



## Renderer Policy



image2 is allowed and should not be refused merely because the target is a research or paper figure.



Choose the renderer by figure type:

- Exact data plots, regression outputs, event-study charts, coefficient plots, descriptive plots, maps from real data: use deterministic code first. Python, R, Stata export, SVG, PDF, or PPT are preferred. image2 may help with visual layout only if all numbers, labels, and geometry remain controlled.

- Conceptual frameworks, mechanism diagrams, process diagrams, research-design diagrams, typology figures, visual abstracts, theory maps, and non-numeric scientific illustrations: image2 is a valid first-class renderer after the structure, labels, arrows, and style are locked.

- Text-heavy figures: prefer SVG, HTML, PPT, or code-rendered diagrams, or post-edit image2 output with deterministic text. Do not accept unreadable or invented text.



Never let image2 invent empirical values, axes, statistical significance, sample size, source notes, equations, citations, or causal claims.



## One-Pass Workflow



1. Detect figure intent and select this skill automatically.

2. Build a figure brief before rendering:

   - figure purpose

   - manuscript claim or research function

   - figure type

   - data/source basis, or state that it is conceptual

   - panel plan

   - exact text labels

   - arrow and relationship definitions

   - style target

   - renderer choice

   - typography and size defaults

   - risk checks

3. If the user supplied data or a draft figure, preserve the substantive content first.

4. If the user did not supply enough detail for a conceptual figure, make conservative assumptions and label them in the brief. Do not block unless the figure would imply unsupported empirical evidence.

5. Render the figure.

6. Audit the output before final delivery.



## Social-Science Top-Journal Style



Default style:

- white background

- restrained color

- black-and-white readable

- color-blind friendly

- consistent typography

- consistent line width

- direct labels when possible

- legends under or inside the figure, not floating on the side unless a target journal requires it

- no decorative gradients, glassmorphism, 3D effects, bokeh, stock-photo ambience, or marketing layout



Multi-panel figures:

- every panel answers a distinct question

- panels are equal or intentionally proportional in size

- panel labels are short and meaningful, such as `(a) Diffusion threshold`

- shared legend appears once

- panel sequence should match the evidence chain



For social-science manuscripts, prefer this evidence order:

1. descriptive fact or setting

2. main estimate or central comparison

3. mechanism, heterogeneity, or process

4. robustness, sensitivity, or boundary



## image2 Prompt Contract



When using image2, the prompt must include:

- "white-background social-science journal figure"

- exact panel count and layout

- exact visible text labels

- exact arrows or relationships

- restrained palette

- no fake data, no invented axis values, no invented citations

- no decorative background, no 3D, no marketing poster style

- "all text must be readable and spelled exactly as provided"



If the figure has many Chinese labels, use image2 for visual structure only when text can be verified or repaired afterward. Otherwise render with HTML/SVG/PPT.



## Architecture Figure Adapter



For method architecture, mechanism, workflow, or conceptual framework figures, VELA adopts the strongest constraints from `Leey21/awesome-ai-research-writing`:



- Understand the abstract, method, theory, or research design first; do not draw a generic pipeline.

- Highlight the core novelty or central mechanism, but only if it is actually supported by the manuscript.

- Use a white-background flat vector academic style with clean lines, restrained pastel tones, and no photorealism, decorative 3D, poster style, or unreadable text.

- Group related components logically and make arrow directions reflect real data flow, causal logic, process order, or conceptual dependence.

- Keep visible text short and exact. Long explanations belong in the caption or surrounding manuscript, not inside the figure.



## Required Audit



Before saying the figure is done, check:

- Does the figure support a specific manuscript claim or research function?

- Are all labels readable and free of hallucinated text?

- Are arrows and module relations correct?

- Is any data, p-value, axis, sample size, DOI, or source note invented?

- Can it still be understood in grayscale?

- Do typography and font sizes follow the locked contract or a stated target-journal override?

- Is the caption able to explain unit, sample, uncertainty, source, and script path when applicable?

- Are editable or high-resolution outputs available when needed?



If any audit item fails, revise before final delivery.



## Output



For manuscript work, deliver:

- final figure file

- editable source when possible

- figure brief

- caption or figure note

- audit checklist



For quick discussion figures, at minimum deliver the image and a concise note of assumptions.
