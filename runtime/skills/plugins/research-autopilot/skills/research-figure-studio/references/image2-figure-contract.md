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
Style preset: social_science_nature_red_blue_rainbow unless another preset is explicitly selected.
Style: restrained, high-quality academic figure, Nature-inspired but adapted to social science; red-blue anchored Nature-style rainbow palette; clean white or very light gray background; high whitespace; thin lines; consistent typography; color-blind friendly; readable in grayscale; no 3D, no decorative background, no poster style.

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
- [Nature deep blue = #1F5AA6; Nature red = #C7363D; cyan = #18A6B8; amber = #F2B84B; orange = #E67E3A; indigo = #273E8E; light grid gray = #E7EBF0]
- [Use red and blue as the primary semantic contrast.]
- [Use cyan, amber, orange and indigo only for extra groups, gradients, maps or multi-series encodings.]
- [Use light gray for axes, grids and panel separators.]

Strict constraints:
- Do not put a formal figure title inside the image; no figure title inside the image.
- Do not put a long caption inside the image.
- Do not overlap text, legends, arrows, points, lines, confidence bands, bars, panel labels, or modules; no overlapping text or legends.
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
- no overlaps among text, legends, arrows, points, lines, modules, and panel labels;
- title and long caption kept outside the image;
- grayscale readability;
- absence of invented empirical claims.

If text is wrong but the visual structure is good, rebuild the text with SVG, HTML, PPT, or image editing rather than accepting the error.
