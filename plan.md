# Module 6 assignment plan (temporary)

Based only on the assignment text supplied in chat. This plan does not assess existing work or assume any data problems. Complete the work individually; choose cleaning rules only after inspecting evidence in your actual data.

## How to use this plan

Work through items 1–3 first. Inspect the original data and write proposed cleaning rules before applying them. Then complete items 4–11, verifying the full dataset rather than only a sample. For item 12, write expected results before checking cleaned output. Finish with reproducibility, limitations, and submission packaging.

In the final checklist, include your project title and student name. For every item, choose **Done / Not applicable / Unresolved** and provide evidence with a file or section reference. Explain every Not applicable response. For every Unresolved response, explain its effect on the analysis. Do not mark an item Done merely because code exists; include its verified result.

## 1. State the project vision and question

- **What to do:** State the project vision, one business question, and the main metric or comparison. Use these to decide which cleaning rules are appropriate.
- **Next step:** Write a short vision statement, a specific question, and a precise definition of the metric or comparison, including its unit and population.
- **Evidence to retain:** A project overview section referenced by checklist item 1.

## 2. Define one row

- **What to do:** Explain what one row represents. Identify the column or combination expected to uniquely identify it, if any. Define this for each relevant table.
- **Next step:** Write the row definition and proposed key before interpreting repeated records as duplicates.
- **Evidence to retain:** Row and key definitions, with full-dataset key checks supporting any uniqueness claim.

## 3. Preserve the source

- **What to do:** Record the data source and version or download date. Keep original files unchanged and explain how to load them. Write cleaned results to separate output files.
- **Next step:** Create a source inventory with source, version/date, original file location, and loading instructions. Establish separate input and output locations before cleaning.
- **Evidence to retain:** Source inventory and loading instructions, also included in the README.

## 4. Inspect columns and types

- **What to do:** Inspect all columns and types. Identify incorrect types, define conversions, count failed conversions, and explain their treatment. Preserve identifiers appropriately rather than automatically converting numeric-looking IDs.
- **Next step:** Build a column inventory of observed and intended types. Write conversion rules, apply only justified conversions, and count failures over the full dataset.
- **Evidence to retain:** Type inventory, conversion rules, failure counts, and how failures were handled. If no conversions are needed, document the inspection result.

## 5. Standardize text

- **What to do:** Inspect text for inconsistencies relevant to the question. Show before/after examples for justified cleaning. Preserve meaningful differences and leading zeros in IDs.
- **Next step:** Examine actual distinct values and representative records, then specify which transformations are justified and which differences must remain.
- **Evidence to retain:** Rules, affected counts, and before/after examples. If text needs no changes, explain why; do not introduce changes merely to populate this item.

## 6. Investigate duplicates

- **What to do:** Count exact duplicate rows and repeated IDs separately. Determine whether repeated keys are legitimate given the row definition. Explain every keep/remove decision.
- **Next step:** Run separate full-dataset checks for identical rows and repeated proposed keys. Inspect any repeats before choosing a rule.
- **Evidence to retain:** Both counts, relevant examples when present, retention/removal rules, and counts affected. A zero finding is evidence, not a reason to invent duplicates.

## 7. Handle missing data

- **What to do:** Report missing counts before and after for each affected column. Explain why values were retained, filled, or dropped, based on the project question.
- **Next step:** Define what counts as missing for each relevant field, profile the full dataset, and write a treatment rule before making changes.
- **Evidence to retain:** Before/after missing-count table, decision reasons, and affected counts. Report a zero finding if no missing values are found.

## 8. Check suspicious values

- **What to do:** Check invalid dates, impossible values, and unusual records using justified rules. Distinguish unusual observations from errors; explain corrections, retained values, and flags.
- **Next step:** Define valid dates and domain constraints from the data meaning, run full-dataset checks, and investigate any flagged records before changing them.
- **Evidence to retain:** Check definitions, counts, examples if present, and reasons for correcting, keeping, or flagging values. Do not assume suspicious values exist.

## 9. Verify merges

- **What to do:** If tables are merged, list keys and the expected relationship, such as one-to-one or many-to-one. Report unmatched keys, row counts before/after, and unexpected extra rows.
- **Next step:** Decide whether a merge is needed for the question. If so, document the keys and relationship, check key uniqueness, and verify match coverage and row counts after merging.
- **Evidence to retain:** Merge specification, unmatched-key counts, before/after row counts, and explanation of any row expansion. If no merge is performed, mark Not applicable and explain that explicitly.

## 10. Reconcile changes

- **What to do:** Report starting and final row counts and account for their difference. Explain changes in important totals after cleaning or merging.
- **Next step:** Maintain a count ledger at each transformation and compare relevant totals before and after. Account for overlapping effects so changes are not counted twice.
- **Evidence to retain:** Reconciliation showing how the starting count becomes the final count, with important totals and reasons for their changes or stability.

## 11. Check calculations

- **What to do:** Explain how missing values affect totals, averages, and denominators. Give the record count for each metric and state how missing group keys are handled.
- **Next step:** Define each metric's numerator, denominator, eligible records, missing-value policy, and grouping policy. Verify calculations and counts on the full dataset.
- **Evidence to retain:** Metric definitions, counts used, missing-value/group-key treatment, and calculation checks. Explain any parts that do not apply to the project.

## 12. Verify individual records

- **What to do:** Check five records, including difficult cases actually present in the data. Write each expected result and its reason before checking the output. Show original values, actual results, and whether they match.
- **Next step:** Select five identifiable records that exercise relevant decisions. Record expectations first, then compare the cleaned results with them and investigate mismatches.
- **Evidence to retain:** A five-record table with record identifier, original value(s), expected result, reason, actual result, and match status. Explain how the records were selected; do not manufacture problems or present synthetic cases as real records.

## 13. Test reproducibility

- **What to do:** Restart and run all code from the unchanged original data with the listed dependencies. Confirm outputs match the submitted files.
- **Next step:** Document the script command and/or notebook restart-and-run-all steps. Execute the complete workflow from a fresh session and compare its outputs with the submission artifacts.
- **Evidence to retain:** Exact commands or notebook steps, dependency versions, output comparisons, and any necessary explanation of controlled randomness or output ordering.

## 14. Document remaining limitations

- **What to do:** List unresolved issues, their potential effects on conclusions, and the information needed to resolve them.
- **Next step:** Review all checks and decision-log entries. Write a limitations section that distinguishes verified findings from remaining uncertainty.
- **Evidence to retain:** Specific limitations, affected metrics or conclusions, and needed information. If no unresolved cleaning issues remain, state that based on the checks without claiming the data is perfect.

## Other required deliverables and final steps

### A. Maintain a cleaning decision log

Start this before applying rules and update it as the work proceeds. Include **rule, reason, and check** for each decision. Make rules fit the question and actual data; explain exceptions. Record changes and verification results so the checklist and row/total reconciliation are traceable.

Suggested columns: decision ID; field/table; rule; reason; exceptions; verification check; result; evidence reference. Include justified decisions to retain values where relevant.

### B. Verify one Codex suggestion or one cleaning decision

If you use Codex, choose one actual suggestion and explain how you checked it against data evidence and project requirements, what the check showed, and whether you accepted, changed, or rejected it. Do not treat Codex's assertion as verification.

If you do not use Codex, explain how you verified one cleaning decision instead. Include the decision, check, result, and supporting evidence in the PDF.

### C. Prepare the data sample

Include **up to 50 cleaned rows**, including difficult cases, and explain the selection method. Keep the sample consistent with the verified cleaned output. Full-dataset verification is still required.

If the data cannot be shared, provide a **clearly labeled synthetic sample** and explain how the instructor can review real results through an approved channel. Do not substitute an unlabeled synthetic sample for actual data.

### D. Prepare code and dependencies

Place your cleaning **scripts (.py)**, **notebook (.ipynb)**, **data sample**, and **dependency files** on your own GitHub branch. Ensure scripts and notebook reflect the same cleaning rules and recreate the submitted results. List the dependencies and versions needed for the documented workflow.

### E. Write the README

Include:

- Data source and version or download date.
- How to obtain/load original inputs while preserving them.
- Dependency setup and exact run instructions.
- Expected output files.
- Sample selection explanation, and sharing/review instructions if applicable.
- Your exact branch name, branch URL, and submitted commit ID.

Use clear references to the evidence and outputs so an instructor can reproduce and inspect the work.

### F. Publish to your individual GitHub branch

Use a different branch from every other student, for example `cleaning-yourname`. Push to your own branch in the **team's project repository**, not `main` and not the shared course repository. Give the instructor repository access.

Finalize files, commit, and push; record the exact submitted commit ID and verify the branch contains the deliverables. Put the exact branch name, branch URL, and submitted commit ID in both the README and PDF. A Git commit cannot contain its own final hash: if adding the README's commit reference requires a later metadata commit, clearly identify the referenced submission commit and ensure it contains the reproducible deliverables.

### G. Assemble and submit the individual PDF

Create **one PDF per student** containing:

- Project title and student name.
- All 14 checklist items, each with status and evidence references.
- Explanations for every Not applicable and Unresolved response.
- Cleaning decision log with rule, reason, and check.
- Five record checks with original, expected, actual, reasons, and match results.
- Verification of one Codex suggestion, or one cleaning decision if Codex was not used.
- Exact GitHub branch name, branch URL, and submitted commit ID.
- Clear references to full-dataset verification, reconciliation, reproducibility, and limitations.

Check that the PDF and repository evidence agree, then submit your own PDF to **Gradescope by the posted deadline**. There is no group submission.

## Final review against the rubric

- **Cleaning decisions (40%):** Rules fit the question and data; reasons and exceptions are explained.
- **Verification (40%):** Checks cover the full dataset; counts and totals reconcile; five record checks are shown.
- **Reproducibility and clarity (20%):** A fresh run recreates submitted results; dependencies, instructions, and evidence are clear.

This temporary plan is a work guide, not a substitute for the completed checklist or any required deliverable.
