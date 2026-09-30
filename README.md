# Data Analyst Portfolio — Vedant Batra

Two reproducible case studies in client analytics and AI adoption, using SQL, Python, Excel and interactive browser dashboards. Built with AI assistance. Independent portfolio; no Gartner affiliation or private client data.

## Explore the projects

| Project | Business question | Evidence |
|---|---|---|
| [Client Retention & Engagement](01-retention/) | Which subscription clients should receive attention before renewal? | 1,400 synthetic clients, 130,148 activity events, time-based model evaluation and outreach prioritisation |
| [AI Adoption & Trust Intelligence](02-ai-adoption/) | Which AI concerns merit a content experiment? | 49,191 public survey responses, usage/trust denominators, audience comparisons and frustration analysis |

Each project includes a case study, metric dictionary, screenshot, interactive dashboard, Excel workbook, editable presentation with speaker notes, executed SQL walkthrough, CSV tables and SQLite database.

**Use the dashboards:** choose Code → Download ZIP, extract the archive and open `index.html`. GitHub displays the HTML source; the downloaded dashboards run offline in your browser.

## Reproduce

Python 3.11+ is required. From the repository root:

```sh
python3 -m pip install -r requirements.txt
python3 source/src/fetch_public_data.py
python3 source/src/pipeline.py --root .
python3 -m unittest discover -s source/tests -p 'test_*.py' -v
```

The download helper retrieves the original Stack Overflow file from the official repository and verifies the recorded SHA-256. The 134 MB raw CSV is excluded from Git; its schema, analysed fields, derived tables and provenance are included. No API key is needed. The analysis overwrites generated analytical tables and databases. `source/src/deliver.py --root .` regenerates the original local portfolio dashboard and learning documents; it does not recreate Office files or this public README. Supplied Office files are editable snapshots authored with the bundled Codex artifact runtime.

## What the results do and do not show

- Retention data is entirely synthetic. At equal outreach capacity, the simple rule-first/value queue finds 35 non-renewals versus 32 for the model. No model superiority or real retention uplift is claimed.
- The public survey download has 49,191 rows versus 49,009 retained responses reported by the publisher. This analysis describes the downloaded file with explicit question denominators. Survey respondents are self-selected developers, not a representative sample of enterprise buyers or Gartner clients.
- These projects demonstrate analytical workflows. No production deployment, live LLM integration, client experiment, measured savings or Power BI implementation is claimed.

## Verification

15 analytical tests and 20 desktop/mobile browser checks passed. A clean-folder run reproduced nine key outputs byte for byte. Workbook formulas and rendered Office previews were reviewed. See [quality report](quality-report.md) and [verification evidence](verification/). Excel and PowerPoint were not directly tested in their native applications.

## Data attribution and licensing

Stack Overflow Developer Survey 2025: [official survey](https://survey.stackoverflow.co/2025/) and [official data repository](https://github.com/StackExchange/Survey/tree/main/packages/archive/2025). The survey database and derived databases remain under [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/); contents are under [DbCL 1.0](https://opendatacommons.org/licenses/dbcl/1-0/). See [SOURCE.json](02-ai-adoption/SOURCE.json) for retrieval date, download URL and hash. Retention inputs are seeded fictional records.
