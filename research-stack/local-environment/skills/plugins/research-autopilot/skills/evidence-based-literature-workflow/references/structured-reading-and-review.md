# Structured Reading and Literature Review

Use this reference when turning a verified literature corpus into structured notes or a literature review section.

## Pre-Reading Candidate Pool

When the user has supplied a paper framework, abstract, empirical result, experimental result, or source literature, do not jump directly into deep reading. First build an about-50-paper candidate pool:

- default split: around 20 Chinese sources and 30 English sources;
- default priority: highly cited and formally published work;
- default index rule: formal included literature must have SCI, SSCI, or CSSCI source evidence;
- default inclusion: source literature that shaped the topic enters the candidate pool, but non-SCI/SSCI/CSSCI source literature remains background or manual-review material unless the user explicitly approves a waiver;
- default expansion: first inspect papers cited by source literature and papers citing it, then expand to adjacent literature.

Screen each source by title, abstract, keywords, venue, citation signal, and relation to the manuscript. Classify it by contribution role:

- `theory`: theoretical foundation, mechanism, concept, or school of thought;
- `research_status`: what existing research has established, debated, or missed;
- `method`: method, identification, data type, or model family;
- `main_variable`: measurement, construct definition, or key explanatory/outcome variable;
- `topic_source`: literature that directly generated the research topic;
- `upstream` or `downstream`: references cited by or citing source literature;
- `adjacent`: related work that may later be excluded.

Before structured reading starts, output:

- candidate literature table;
- SCI/SSCI/CSSCI status or manual-review reason for each formal candidate;
- acquired PDF list;
- missing or blocked PDF list;
- rejected or low-priority list with reasons.

## Structured Reading Table

Recommended columns:

- `reference_id`
- `authors_year`
- `title`
- `venue`
- `doi_or_exemption`
- `index_status`
- `index_evidence`
- `pdf_path`
- `research_question`
- `theory_or_concepts`
- `data_sample`
- `method`
- `main_findings`
- `limitations`
- `relevance_to_project`
- `claim_supported`
- `candidate_evidence_location`
- `reading_status`

Stable statuses:

- `read_complete`
- `read_partial`
- `metadata_only`
- `excluded`

## Per-Article Note

Use this compact structure:

```markdown
# [Author Year] [Short Title]

## Why Included

## Research Question

## Theory and Concepts

## Data and Method

## Main Findings

## Limits

## Relevance to Our Manuscript

## Candidate Evidence Sentences
```

## Review Writing Rules

1. Start from the manuscript's research problem, not from chronological listing.
2. Keep seed papers central when the user's project is built as theoretical or methodological dialogue with them.
3. Distinguish theory foundation, empirical research status, method/measurement literature, and remaining gap.
4. Use verified citations only.
5. Do not cite a paper for a claim if the structured note only says it is topically related.
6. For method papers, check whether the method's evidence strength matches the manuscript's wording.
7. For social-science writing, use dense academic prose and avoid empty connective phrases.

## PEEL Paragraph Template

```markdown
[Point] 本段提出的判断。
[Evidence] 已核验文献中的具体发现或方法。
[Explanation] 这些证据为什么支持该判断。
[Link] 该判断如何推进本文问题、假设或方法选择。
```

Do not label PEEL elements in the final manuscript unless the user asks for teaching notes.
