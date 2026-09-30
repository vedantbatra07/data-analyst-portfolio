# Quality and verification

Completed 1 October 2026. These are independently presented portfolio case studies, built with AI assistance, for the supplied Gartner requisition 113297. They are not Gartner work or evidence of achieved client impact.

## Analytical checks

15 automated tests pass. Evidence: verification/analysis-tests.txt and source/tests/test_portfolio.py.

- Unique keys and foreign keys reconcile across synthetic clients, contracts, activity and support.
- Independent pandas calculations agree with SQL event windows, support status and contract totals.
- Time boundaries, temporal cohorts and unknown upcoming outcomes are checked. Upcoming observations stop at their snapshot cutoff.
- Model training uses earlier contracts and training-only preprocessing. Confusion-matrix calculations, missing denominators and feature selection are checked.
- Survey aggregates reconcile to respondent data. Multiple-choice answers are deduplicated and use the relevant question denominator.
- Malformed identifiers/categories are rejected; Wilson interval bounds are tested.

A clean temporary directory was populated with only the packaged source and original public input files. The pipeline, all 15 tests and dashboard/document generation ran successfully. Nine key JSON, CSV and HTML outputs matched the delivered outputs byte for byte. Evidence: verification/reproducibility.json and reproducibility-log.txt.

## Dashboard checks

20 browser checks pass in headless Brave/Chromium at desktop and phone widths (1,440 and 390 pixels). Checks include headline values, filtering, navigation, CSV download, method disclosure, empty selections and absence of JavaScript errors. The files were tested directly from disk without a server or external requests. Both layouts were visually inspected. Evidence: verification/browser-check.json.

These checks do not constitute exhaustive browser, accessibility or device certification.

## Excel and presentations

Both workbooks have two sheets, working formulas and native charts. Eleven headline formula results were reconciled to analytical outputs. The retention scenario recalculated after a changed assumption; the survey workbook handled a zero denominator. The original inputs were restored. Formula error scans and all four sheet previews were inspected.

Both five-slide decks preserve the selected Simple Dark Mode template. Each includes an editable native chart with an embedded workbook and speaker notes. All ten slides were rendered and visually inspected. Package, layout, font-policy and chart validators passed; final file hashes agree with their validation receipts.

Evidence: verification/*formula-scan.json and *deck-validation.json. The files were not opened in native Microsoft Excel or PowerPoint. Rendering or font substitution may differ in those applications. The presentation template's embedded font decoding produced a warning in the authoring runtime; previews used the available Helvetica Neue font and were inspected.

## Findings and limits that must accompany the projects

**Retention:** all 1,400 clients and 130,148 activity events are synthetic. The model is a teaching baseline, evaluated on 406 later-period contracts. At the same 81-account outreach capacity, the model finds 32 non-renewals and the rule-first/value queue finds 35. Do not claim model superiority. Flagged upcoming annual contract value is exposure, not savings or recovered revenue. A controlled pilot is proposed; none was run.

**AI adoption:** the Stack Overflow public download contains 49,191 rows, while its published methodology reports 49,009 retained responses. The unexplained 182-row difference is explicitly recorded. This analysis uses the downloaded file and question-level denominators; it does not claim exact replication of the published survey. Respondents are self-selected developers, not Gartner clients or a representative enterprise buyer sample. Missing usage answers are 31.5% of downloaded rows. Descriptive uncertainty intervals do not remove selection or nonresponse bias.

Original public data, its SHA-256, source links and licensing details are included in 02-ai-adoption/SOURCE.json. The database and its derivatives remain subject to ODbL 1.0; contents are under DbCL 1.0. See https://opendatacommons.org/licenses/odbl/1-0/ and https://opendatacommons.org/licenses/dbcl/1-0/.

The analytics pipeline uses Python, NumPy, pandas and SQLite. The interactive dashboards are standalone HTML, not Power BI. No paid service, live LLM endpoint, public deployment, real stakeholder experiment or internship application was implemented. Optional Office rebuilding needs the bundled Codex artifact-tool runtime and the original presentation template; the analytical pipeline and HTML are independently reproducible with the supplied Python requirements.

## Before an interview

Open the dashboards and Office files on the computer you will present from. Work through interview-guide.md, reproduce the key SQL results, and rehearse the speaker notes in your own words. Explain AI assistance, your personal contribution and the limits of each result accurately.
