# Citation Evidence Audit



Use this reference when checking whether manuscript citations are semantically supported by cited sources.



## Core Standard



The unit of audit is not "paper appears relevant." The unit is:



`manuscript sentence -> cited reference -> complete body-text evidence sentence -> support judgment`.



## Evidence Rules



Accept:



- complete sentences from the article/book body;

- continuous complete-sentence groups when one sentence alone is insufficient;

- method, theory, findings, or conclusion sentences written by the cited authors.



Reject as final evidence:



- title;

- abstract;

- keywords;

- table title;

- figure caption;

- page header/footer;

- reference list;

- another author's claim quoted or cited by the source;

- the cited author's untested hypothesis, expectation, or research question when the manuscript needs an empirical finding or established theoretical claim;

- a literature-review sentence in which the cited author is summarizing another work, unless the manuscript is explicitly citing it as that author's review of the field;

- incomplete OCR fragments;

- whole pages or large unbounded passages;

- text that only shares keywords with the manuscript claim.



## Sequential Reading and Marking Rules



Do not batch mark. Process each cited source and each manuscript citation deliberately:



1. Open one cited PDF at a time.

2. Read the relevant body-text section before selecting evidence.

3. Confirm that the evidence sentence expresses the same meaning as the manuscript citation use.

4. Confirm that the sentence is the cited author's own claim, finding, method statement, or theoretical definition.

5. Reject sentences that only report another source's claim, even if the sentence contains the same keywords.

6. Reject hypothesis sentences such as "we expect", "we hypothesize", or "we propose to test" when the manuscript uses the citation as evidence of a result.

7. Mark the exact complete sentence or continuous complete-sentence group; do not mark isolated words, broken lines, half sentences, or non-contiguous sentence fragments.

8. Record the decision before moving to the next citation.

9. If the same source supports multiple manuscript claims, assess each claim separately; do not reuse a generic paragraph for all claims.

10. If no direct sentence exists, mark `unsupported` or `partially_supported` and propose a manuscript rewrite or replacement citation.



## Audit Table Columns



Minimum fields:



- `citation_id`

- `manuscript_sentence`

- `reference_key`

- `pdf_path`

- `page_number`

- `evidence_sentence`

- `evidence_context_note`

- `support_status`

- `required_revision`

- `annotated_pdf_path`

- `screenshot_path`

- `reviewer_note`

- `reviewed_at`



Recommended support statuses:



- `supported`

- `partially_supported`

- `unsupported`

- `no_pdf_available`

- `metadata_only`



## Procedure



1. Extract all manuscript sentences with citations.

2. Split compound manuscript claims into separate auditable claims.

3. Open the cited PDF and locate candidate sections using keywords only as navigation.

4. Read surrounding paragraphs before deciding support.

5. Select the shortest complete sentence or continuous complete-sentence set that directly supports the claim.

6. Highlight the complete evidence sentence in the PDF. The highlight should cover sentence boundaries, not just keywords or a large page region.

7. Generate a screenshot showing the highlighted sentence and nearby body text. The screenshot must let a third party see both the evidence sentence and its context.

8. Record the support judgment and required revision.

9. For `partial` and `unsupported`, revise the manuscript, replace the citation, or delete the claim.

10. Re-check consistency after manuscript revisions.



## PDF Marking Protocol



Treat PDF marking as an auditable production step, not as a visual convenience.



### Work Area



- Never annotate the source PDF, user-provided original, or raw download in place.

- Copy or write marked files only under the project output directory, normally a per-paper round folder such as `pdf_evidence_annotations/per_paper_rounds/roundNNN_author_year/`.

- Keep source PDFs, clean working copies, annotated PDFs, screenshots, manual notes, audit CSV/XLSX/DOCX, and accepted registry paths separate.

- If a source PDF already contains annotations, create a clean working copy or strip inherited annotations before marking. Acceptance requires `inherited_annotation_count=0`.

- Do not process source data or source PDFs directly when the user has asked to preserve originals; always use copied working files.



### One-Paper-One-Round



- Mark one cited paper at a time. Do not batch-mark several papers from keyword hits.

- A round belongs to one source and one current citation table state. If a manuscript claim or evidence sentence changes, rebuild a new round rather than silently editing old audit outputs.

- If the same paper supports multiple manuscript claims, create separate evidence IDs and judge each claim separately. Reusing the same evidence sentence is allowed only when it directly supports each narrowed claim.

- Record failed rounds instead of overwriting them; the accepted registry should point only to the latest round that passed review.



### Evidence Location



- Evidence must be in the cited author's body text.

- Reject abstract, title, keywords, table titles, figure captions, page headers, footers, footnotes used as source chains, reference lists, and purely bibliographic text.

- Reject a sentence that merely reports another author's finding unless the manuscript explicitly cites the source as a review/synthesis.

- Reject author hypotheses or research questions when the manuscript needs an empirical finding, method rule, or established theoretical claim.

- Tables and figures may guide reading, but final evidence should still be body-text sentences unless the user explicitly asks for table/figure evidence and the audit marks that exception.



### Sentence Boundary Rules



- Highlight exactly one complete sentence or a continuous complete-sentence group.

- Include sentence-final punctuation. A highlight that stops before the final period/句号 is incomplete.

- Do not start after the true sentence beginning, even if the semantic core begins later.

- Do not include the previous sentence tail, next sentence start, unrelated paragraph text, or reference-list fragments.

- Do not mark isolated keywords, half sentences, non-contiguous fragments, or whole pages.

- When a sentence starts mid-line after another sentence ends, start at the first character of the evidence sentence, not at the line's left margin.

- When a sentence ends mid-line before another sentence starts, stop at the sentence-final punctuation, not at the line's right margin.

- Search text used to locate evidence is not the evidence boundary. A search-hit highlight is acceptable only when visual inspection shows it covers the complete evidence sentence or continuous complete-sentence group.

- Footnote numbers may remain inside a highlighted sentence only when needed for exact source-coordinate alignment. Do not treat footnote content as final evidence unless the audit explicitly marks that exception.



### Automatic vs Manual Coordinates



- Automatic text-span matching is acceptable only after visual inspection shows exact sentence boundaries and body-text location.

- Use manual coordinate overrides when automatic marking:

  - starts mid-sentence;

  - includes previous or next sentence text;

  - misses final punctuation;

  - selects abstract, reference list, page header/footer, table/figure material, or footnote material;

  - fails because of OCR, full-width characters, hyphenation, or multi-column layout.

- Manual overrides should record the page number and rectangles used, with a boundary note explaining why manual marking was needed.

- After manual marking, regenerate screenshots and inspect them again before review.

- Accepted statuses must distinguish full-sentence evidence from phrase fallback. Rows such as `highlighted_phrase_fallback`, `search_not_found_manual_review`, or `manual_review` remain unresolved until the highlight is manually expanded, the OCR/manual rectangles cover the full sentence, or the manuscript claim is narrowed and rechecked.

- Token matching may normalize hyphenation, ligatures, full-width characters, and line breaks for locating candidate text, but visual inspection of the rendered screenshot decides acceptance.



### Visual Inspection



- Inspect every new or revised screenshot, not just a sample, when the user requires strict audit.

- The screenshot must show the highlight plus enough surrounding context to verify body-text location.

- Look specifically for: abstract pages, reference-list pages, incomplete punctuation, carried-over previous sentence tails, next-sentence spillover, page headers/footers, and oversized highlights.

- Also check for phrase-only highlights and stale screenshots from earlier audit rounds; both are defects in a strict final package.

- If any boundary or source-location defect is visible, rebuild the round before external review.



### Review Gate



- Run two independent reviews for each completed marking round when the user requires validation:

  - locator/boundary/source review: PDF page, body-text location, complete sentence boundaries, paths, inherited annotations;

  - semantic review: whether evidence supports the exact manuscript claim without overclaiming.

- Both reviews must PASS before a paper enters the accepted registry.

- If either review FAILs, revise the manuscript claim, evidence sentence, or PDF highlight; generate a new round; rerun the two reviews.

- Do not count a citation as accepted because a previous round passed if the manuscript claim, evidence sentence, or PDF boundary changed later.



### Registry and Coverage



- Maintain an accepted-paper registry with `citation`, `title`, `accepted_round`, `evidence_ids`, `accepted_audit_path`, `accepted_annotated_pdf_dir`, and `accepted_screenshot_dir`.

- The accepted registry must cover exactly the current citation table evidence IDs: no missing, duplicate, or extra IDs.

- Every accepted audit row should have an accepted full-evidence annotation status such as `highlighted_full_sentence`, `ocr_rect_marked`, `supported_highlighted`, or a documented project-equivalent status, plus `inherited_annotation_count=0`, existing annotated PDF path, and existing screenshot path.

- When references are added to a manuscript after drafting, add them to the citation table and run the same PDF evidence marking gate. Do not leave a paper only in the reference list.

- Regenerate accepted registry and coverage tables from the current manuscript after any citation wording, citation placement, evidence sentence, or claim-scope change. Do not carry over a previous PASS decision without rerunning the affected paper.

- Before final delivery, delete or quarantine stale generated notes, screenshots, and annotated PDFs from prior rounds. The final package should not contain old manual-review scan notes or screenshots that point to superseded claims.



## PDF Marking Requirements



- Save a marked copy under `citation_annotated_pdfs/`.

- Save one screenshot per evidence item or per tightly related evidence group under `citation_evidence_screenshots/`.

- Use page numbers from the PDF viewer or rendered page consistently and record them in the audit table.

- If a PDF cannot be edited, document the technical reason, save a screenshot with the evidence sentence visible, and record the missing annotated PDF as a fallback rather than silently calling the annotation complete.

- After marking, visually inspect representative screenshots. If the highlighted text is broken, starts mid-sentence, ends before the sentence boundary, or includes irrelevant paragraphs, redo the marking.

- A final accepted `citation_evidence_records.csv` must not contain unresolved statuses such as `highlighted_phrase_fallback`, `search_not_found_manual_review`, `manual_review`, or stale intermediate statuses unless they are reported as explicit unresolved blockers. Text-layer accepted rows should be full-sentence rows, not search-hit rows.



## Common Repairs



- If the source supports correlation but the manuscript claims causality, revise to "相关", "关联", or "经验联系".

- If the source supports a national case but the manuscript generalizes globally, add scope limits.

- If the source supports a method family but not the exact estimator, cite a method-specific source.

- If the source is only a seed-paper context, cite it for the problem framing, not for an empirical claim it did not test.



## Final Package



Create:



```text

citation_evidence_audit.xlsx

citation_evidence_audit.docx

citation_annotated_pdfs/

citation_evidence_screenshots/

citation_manual_article_notes/

citation_manual_review_queue.csv

citation_evidence_rule.md

citation_manual_review_completion_summary.md

two_agent_review_summary.md

agent_review_reports/

```



For multi-round audits, merge the final supported records into:



```text

00_最终核验包/

  citation_evidence_audit_final.csv

  citation_evidence_audit_final.xlsx

  citation_evidence_audit_final.docx

  citation_evidence_records.csv

  citation_sentences.csv

  citation_manual_review_queue.csv

  citation_evidence_final_summary.md

```
