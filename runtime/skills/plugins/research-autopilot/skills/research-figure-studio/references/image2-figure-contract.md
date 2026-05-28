# image2 Figure Contract



Use image2 for research figures when structure and labels can be specified precisely.



## Allowed Uses



image2 is appropriate for:

- conceptual framework figures;

- mechanism diagrams;

- research workflow diagrams;

- visual abstracts for academic presentations;

- qualitative process models;

- stylized ABM or network mechanism illustrations;

- polishing a white-background explanatory figure after the logical structure is fixed.



image2 can also be used for an empirical figure's visual framing, but it must not invent or alter data.



## Not Allowed



Do not use image2 to invent:

- numeric results;

- axis values;

- p-values or confidence intervals;

- sample sizes;

- DOI or source notes;

- quotations;

- author names or titles;

- causal claims not in the manuscript;

- statistical model outputs.



## Prompt Template



Use a prompt shaped like this:



```text

Create a white-background social-science journal figure suitable for manuscript review.



Figure type: [mechanism / research design / conceptual framework / workflow / multi-panel evidence figure].

Audience: social-science journal reviewers.

Style: restrained, high-quality academic figure, Nature-inspired but adapted to social science; clean white background; thin lines; consistent typography; color-blind friendly; readable in grayscale; no 3D, no gradients, no poster style, no decorative background.



Canvas: [16:9 / journal single-column / journal double-column].

Layout: [exact panel count and arrangement].

Panel labels: [exact labels].

Visible text labels, spelled exactly:

- [label 1]

- [label 2]

- [label 3]



Connections:

- [A -> B means ...]

- [dashed feedback line from ... to ... means ...]



Color mapping:

- [blue = ...]

- [teal = ...]

- [orange = ...]

- [gray = ...]



Strict constraints:

- Do not invent any data, numbers, citations, DOI, p-values, sample size, axis ticks, or source notes.

- Do not add extra labels not listed above.

- All text must be readable and spelled exactly as provided.

- Keep all modules aligned with even spacing.

```



## After image2



Always inspect the output:

- text accuracy;

- arrow direction;

- panel structure;

- label completeness;

- grayscale readability;

- absence of invented empirical claims.



If text is wrong but the visual structure is good, rebuild the text with SVG, HTML, PPT, or image editing rather than accepting the error.
