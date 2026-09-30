"""Build offline dashboards, case studies and portfolio documentation from results."""
import json, shutil, hashlib
from pathlib import Path
import pandas as pd

SRC=Path(__file__).resolve().parents[1]
WORK=SRC.parents[1]
OUT=WORK/'outputs/analyst-portfolio'
def load(name):return json.loads((OUT/name/'analysis.json').read_text())
def put(path,text):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text.strip()+'\n')
def pct(x):return f'{x:.1%}'
def build():
    r=load('01-retention'); a=load('02-ai-adoption');s=r['summary'];t=a['summary']
    template=(SRC/'src/dashboard.html').read_text()
    configs=[('01-retention','retention','Client retention & engagement','01 / Product & client analytics','Where should a subscription business focus its next client conversations?','Synthetic case study · 1,400 fictional clients · Historical renewals in 2025 · Upcoming snapshot: 31 Dec 2025',r),
        ('02-ai-adoption','ai','AI adoption & trust','02 / Technology & demand intelligence','Understand the gap between using AI and trusting it, then turn the evidence into content experiments.','Public survey data · Stack Overflow 2025 · Independent analysis of 49,191 downloaded responses · Not Gartner client data',a)]
    for folder,key,title,kicker,intro,disclosure,data in configs:
        html=template
        for placeholder,value in {'TITLE':title,'PROJECT':key,'KICKER':kicker,'INTRO':intro,'DISCLOSURE':disclosure,'DATA':json.dumps(data,ensure_ascii=False).replace('</',r'<\/')}.items():html=html.replace('__'+placeholder+'__',value)
        put(OUT/folder/'dashboard.html',html)
    put(OUT/'index.html',f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Fieldnotes · Analyst portfolio</title><style>
    *{{box-sizing:border-box}}body{{margin:0;background:#101314;color:#f4f3ed;font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}main{{max-width:1120px;margin:auto;padding:65px 7%}}.label{{color:#caf37c;font-size:12px;letter-spacing:2px}}h1{{font-size:clamp(40px,6vw,68px);line-height:1.06;letter-spacing:-2px;margin:24px 0}}p{{color:#acb7b5;max-width:700px}}.projects{{display:grid;grid-template-columns:1fr 1fr;gap:24px;margin:50px 0}}article{{border-top:1px solid #55605b;padding:26px 0}}h2{{font-size:27px;line-height:1.2;font-weight:500}}a{{color:#caf37c}}.go{{display:inline-block;background:#caf37c;color:#152010;padding:11px 17px;border-radius:6px;text-decoration:none;margin:20px 0}}.stat{{font-size:43px;color:#f4f3ed}}small{{color:#acb7b5;display:block}}footer{{border-top:1px solid #353c3d;padding-top:24px;display:flex;gap:20px;flex-wrap:wrap;font-size:13px}}@media(max-width:650px){{.projects{{grid-template-columns:1fr}}main{{padding:32px 24px}}}}</style><main><div class="label">FIELDNOTES / DATA ANALYST PORTFOLIO</div><h1>Business questions.<br>Evidence you can explain.</h1><p>Two complete analytical case studies prepared for the Gartner Associate Data Analyst Intern role. Explore the findings, inspect the assumptions and follow each result back to its source.</p><div class="projects"><article><div class="label">01 / SYNTHETIC BUSINESS CASE</div><h2>Client retention<br>& engagement</h2><div class="stat">{s['historical_clients']:,}</div><small>historical contracts and {s['activity_events']:,} activity events</small><p>Relational SQL, renewal analysis, an interpretable model and a prioritised outreach queue.</p><a class="go" href="01-retention/dashboard.html">Explore retention ↗</a><br><a href="01-retention/interview.pptx">Presentation</a> &nbsp; <a href="01-retention/analysis.xlsx">Excel analysis</a></article><article><div class="label">02 / PUBLIC SURVEY STUDY</div><h2>AI adoption<br>& trust intelligence</h2><div class="stat">{t['respondents']:,}</div><small>responses in the downloaded public survey</small><p>Survey cleaning, careful denominators, audience comparisons and evidence for content experiments.</p><a class="go" href="02-ai-adoption/dashboard.html">Explore AI adoption ↗</a><br><a href="02-ai-adoption/interview.pptx">Presentation</a> &nbsp; <a href="02-ai-adoption/analysis.xlsx">Excel analysis</a></article></div><footer><a href="START_HERE.md">Start here</a><a href="interview-guide.md">Interview preparation</a><a href="README.md">Reproduce the analysis</a><a href="quality-report.md">Data quality & verification</a></footer><p style="font-size:12px">Independent portfolio. No Gartner affiliation, private client data or proven business impact. Built with AI assistance; learning notes explain how to review and present the work honestly.</p></main></html>''')
    put(OUT/'01-retention/case-study.md',f'''
# Client Retention & Engagement Analytics

## Decision and audience
An account-management lead at a fictional research subscription platform has limited time for outreach. Which clients should receive attention before renewal? This is a synthetic case study, not analysis of Gartner clients.

## Scope
- {s['clients']:,} fictional clients, {s['historical_clients']:,} historical contracts and {s['upcoming_clients']} upcoming contracts.
- {s['activity_events']:,} activity events across research reads, webinars and expert sessions.
- Fixed seed 113297. One annual contract per account; no expansion, contraction or repeat renewal modelling.
- USD denotes hypothetical annual contract value, not recognised revenue or profit.

## Method
Four tables feed SQLite views. Activity and support facts aggregate independently before joining contracts. Feature snapshots use only information known 60 days before renewal. Jan–Aug 2025 renewals train the model (n={s['training_n']}); Sep–Dec form the holdout (n={s['holdout_n']}). Each client appears in only one cohort.

The transparent rule flags zero activity over 30 days, at least two open support requests, or a 40% activity decline from at least five prior events with no expert session in 60 days. A five-feature, L2-regularised logistic model provides an interpretable ranking comparison. Training-set means and standard deviations scale its features. Hyperparameters are fixed, and no holdout outcome is used for fitting or selecting features.

## Findings
1. **{pct(s['renewal_rate'])} of historical clients renewed**: {int(s['renewal_rate']*s['historical_clients']):,} of {s['historical_clients']:,} contracts. Renewed annual value is ${s['renewed_value_usd']:,} / ${s['eligible_value_usd']:,} eligible, or {pct(s['value_renewal_rate'])}.
2. The rule finds **{s['rule']['tp']} of {s['rule']['nonrenewals']} holdout non-renewals**. It flags {s['rule']['flagged']} accounts, including {s['rule']['fp']} that renew. Precision is {pct(s['rule']['precision'])}; recall is {pct(s['rule']['recall'])}.
3. At **{s['capacity']['flagged']} outreach slots**, the model captures {s['capacity']['tp']} non-renewals ({pct(s['capacity']['precision'])} precision). Rule-first, then highest contract value captures {s['rule_capacity']['tp']} ({pct(s['rule_capacity']['precision'])}). Random selection would have an expected {pct(s['rule']['baseline'])} non-renewal share. This single simulated holdout does not prove superiority or actual campaign impact.
4. The model's AUC is **{s['model']['auc']:.3f}**. Its fixed 0.5 probability threshold catches only {s['model']['tp']} non-renewals, illustrating why accuracy or a default threshold alone is a poor business decision criterion.
5. The upcoming queue flags **{s['flagged_upcoming']} accounts** representing ${s['flagged_contract_value_usd']:,} of annual contract exposure. This is not predicted recoverable revenue.

## Recommendation and rollout proposal
Start with human review of rule explanations. Confirm that ticket and activity data are complete, then test a fixed outreach script on a random subset of comparable flagged accounts. Keep a usual-service control group. Record time spent and complaints. At maturity, compare renewal rates with confidence intervals and contribution economics. Choose an effect size and sample size before the real experiment. No experiment was run in this portfolio.

## Limitations
The generator embeds noisy engagement and renewal relationships; these findings cannot validate real customer behaviour. Scores are uncalibrated simulation estimates. The contract-value ranking is a priority heuristic, not an estimate of incremental benefit. No real retention improvement or savings were measured. Model performance may shift across renewal periods.

## Presentation route
Open dashboard.html: Overview → Validation → Outreach → Method. Show a filter, explain one denominator, inspect a false positive and finish with the proposed experiment.
''')
    put(OUT/'02-ai-adoption/case-study.md',f'''
# AI Adoption & Trust Intelligence

## Decision and audience
A technology-content team wants to identify audiences and practical AI topics worth testing. The study analyses developer survey responses as an external signal, not as Gartner client demand.

## Source and scope
[Stack Overflow 2025 Developer Survey](https://survey.stackoverflow.co/2025/), downloaded 30 September 2026 from the publisher's [official repository](https://github.com/StackExchange/Survey/tree/main/packages/archive/2025). The survey ran 29 May–23 June 2025. Recruitment primarily used Stack Overflow channels. See the [methodology](https://survey.stackoverflow.co/2025/methodology).

The downloaded file contains **{t['respondents']:,} rows**, while the methodology reports 49,009 retained responses. The 182-row discrepancy remains unresolved. We do not invent an exclusion rule. All results here describe this downloaded file and explicit question-level populations. SOURCE.json records SHA-256 and retrieval details.

## Method
Validate unique respondent IDs and allowed answer categories. Preserve missing answers. Separate current AI usage from planned use. Define low trust as Somewhat distrust or Highly distrust; keep neutral answers in the denominator. Analyse low trust only among current users answering the trust question. Preserve blank work experience as Unknown because the questionnaire tells zero-experience respondents to leave it blank. Split frustration responses into a respondent/category bridge table and deduplicate selections.

## Findings
1. **{pct(t['current_adoption'])} currently use AI** among {t['usage_answered']:,} respondents answering usage: {t['current_users']:,} current users. Another {t['planned_users']:,} plan to use it soon. Current-or-planned usage is {(t['current_users']+t['planned_users'])/t['usage_answered']:.1%}, which should not be described as current usage.
2. **{pct(t['low_trust_share'])} of responding current users report distrust**: {t['low_trust_users']:,} / {t['users_answering_trust']:,}. This does not share the denominator of the website's overall trust statistic.
3. **{a['quality']['missing_usage']:,} respondents have no usage answer** ({a['quality']['usage_missing_rate']:.1%} of downloaded rows). Treating those answers as No would depress the adoption rate incorrectly.
4. The most frequently selected frustration among responding current users is **{a['frustrations'][0]['frustration']}**, selected by {a['frustrations'][0]['respondents']:,} / {a['frustrations'][0]['denominator']:,} ({a['frustrations'][0]['share']:.1%}). Multiple selections mean shares need not add to 100%.

## Recommended content experiments
- Test an answer-verification guide with current users who distrust outputs. Measure usefulness and completion before inferring demand.
- Test a debugging workshop with developers reporting debugging friction. Use a controlled exercise to measure task time, while recording code correctness.
- Test an explanation-focused session with developers reporting difficulty understanding generated code. Use a short comprehension assessment.

Audience segment percentages are descriptive; compare denominator sizes and nonresponse before prioritising. Prefer segments with at least 100 current users answering trust for exploratory comparisons. This is a reporting convention, not a power calculation or statistical validity guarantee.

## Limits and next evidence
Self-selection and missing answers constrain generalisation. Employer size describes a respondent's employer, not a sampled company. Multiple respondents may share an employer. Wilson intervals are descriptive and do not remove selection bias. Associations do not prove causation. Validate hypotheses with a consented audience study and actual content engagement before allocating a material budget. No LLM or sentiment model is needed to relabel the questionnaire's existing categories.

## License
Stack Overflow survey database: ODbL 1.0; contents: DbCL 1.0. Derived survey data retains these terms and attribution. Source and transformation scripts accompany this work.
''')
    put(OUT/'01-retention/metrics.md','''
# Retention metric dictionary

| Metric | Definition | Grain / caveat |
|---|---|---|
| Client renewal rate | Renewed contracts / contracts due in 2025 | One annual contract per client; exclude upcoming |
| Annual value renewed | Sum of annual contract value where renewed = 1 | USD, not recognised revenue |
| Value renewal rate | Annual value renewed / value of all contracts due | No expansion/contraction; not net revenue retention |
| Activated in 30 days | At least one activity event in [start, start + 30 days) | Single event suffices; demo definition |
| Recent activity | Events in (cutoff − 30 days, cutoff] | Cutoff = renewal − 60 days |
| Prior activity | Events in (cutoff − 60 days, cutoff − 30 days] | No window overlap |
| Decline | 1 − recent / prior | NULL if prior = 0; negative means growth |
| Expert sessions | Expert events in (cutoff − 60 days, cutoff] | No future information |
| Service breadth | Distinct services used in prior 60 days | Zero if no events |
| Open tickets | Opened on/before cutoff and unresolved or resolved after cutoff | Known state at decision time |
| Precision | True non-renewals among flagged / all flagged | NULL if no flags |
| Recall | True non-renewals among flagged / all non-renewals | NULL if no non-renewals |
| AUC | Probability a non-renewal receives a higher score than a renewal, half credit for ties | Ranking only |
| Brier score | Mean squared error of predicted non-renewal probability | Lower is better; no real-world calibration claim |
| Flagged value | Sum of annual value for rule-flagged upcoming contracts | Exposure, not recoverable revenue |

Raw tables: clients (client_id PK), contracts (client_id PK/FK), activity (event_id PK, client_id FK), support (ticket_id PK, client_id FK). CSV data types and NULL handling follow source/pipeline.py. Upcoming outcome is blank; observed historical outcomes are 0 or 1. Model scores use a training-only scaler. Data/features.csv is one row per client, computed by SQL.
''')
    put(OUT/'02-ai-adoption/metrics.md','''
# AI adoption metric dictionary

| Metric | Numerator | Denominator / definition |
|---|---|---|
| Current adoption | AISelect begins Yes, | All nonmissing AISelect answers |
| Planned adoption | No, but I plan to soon | All nonmissing AISelect answers |
| Low-trust user share | Current users with Somewhat distrust or Highly distrust | Current users with any nonmissing AIAcc answer |
| Usage missing rate | Missing AISelect | All downloaded rows |
| Frustration share | Unique current users selecting a category | Current users with any nonmissing AIFrustration |
| Experience band | WorkExp grouped 0–5, 6–10, 11–20, 21+ | Blank remains Unknown; no imputation |
| Wilson interval | 95% binomial interval for low-trust proportion | Descriptive only; does not correct nonrandom sampling |

respondents has one row per ResponseId. frustrations has one row per unique respondent_id/frustration pair. role comes from DevType (single primary role in this questionnaire). organization_size is OrgSize. NULL is a missing survey answer, not a negative answer. current_user/low_trust flags may be zero when source answers are missing, but denominators always explicitly require answered questions. All conditional comparisons must retain this rule.

The dashboard uses a count cube grouped by experience, role and employer size. It sums numerators and denominators before division; it never averages subgroup percentages. Small intersections can be empty. No respondent-level free text is embedded in the dashboard.
''')
    put(OUT/'START_HERE.md',f'''
# Your two analyst portfolio projects

Open **index.html** in a browser. Both dashboards run offline with no installation or account.

1. Explore **Client Retention & Engagement**. Read case-study.md, inspect Validation, then open interview.pptx and its speaker notes.
2. Explore **AI Adoption & Trust**. Try experience and role filters. Read the Method page before using its percentages in an interview.
3. Open each **analysis.xlsx** for formula-based Excel analysis. The retention workbook includes an editable outreach scenario; the AI workbook calculates rates from aggregate source counts. Full row-level data is in the data folders and SQLite databases.
4. Read **interview-guide.md**. Reproduce key SQL results and explain the limitations in your own words.
5. Use **resume-bullets.md** after you have personally reviewed the work. This package was built with AI assistance; do not claim independent implementation, real clients, measured savings or tools you did not use.

## What you have
- Two interactive dashboards with filters and CSV exports.
- Two Excel workbooks with formulas and native charts.
- Two editable five-slide presentations with speaker notes.
- Source SQL, Python pipeline, model parameters, data dictionaries, case studies and tests.
- Public-source provenance and an explicit synthetic-data disclosure.

## Application context
Tailored to your supplied Gartner IPA Associate Data Analyst Intern description, requisition 113297. The description states an October 9, 2026 deadline, a 2028 graduation requirement, proximity to Irving, TX and US work authorisation. These projects demonstrate skills; they do not establish eligibility or guarantee selection.

## Practical limits
The dashboards are standalone HTML, not Power BI files. Excel and slides are supplied as editable Office files. No project has been publicly published, no application has been submitted, and no paid service is connected.
''')
    put(OUT/'README.md','''
# Fieldnotes: analyst portfolio

Independent, AI-assisted portfolio for Gartner Associate Data Analyst Intern requisition 113297. No Gartner affiliation. No private client data.

## Open the result
Double-click index.html. Each project includes dashboard.html, analysis.xlsx, interview.pptx, case-study.md, metrics.md, analysis.json, analysis.sqlite and data/.

## Reproduce the analysis
Requirements: Python 3.11+, NumPy and pandas. Tested versions are recorded in environment.json. SQLite is included in Python. The source code uses no API key.

From the extracted portfolio directory:
```
python3 source/src/pipeline.py --root .
python3 -m unittest discover -s source/tests -p 'test_*.py' -v
```
The package includes the original public survey at 02-ai-adoption/data/stackoverflow_2025.csv. SHA-256 appears in SOURCE.json. Outputs overwrite only the two portfolio analysis directories. The simulation uses seed 113297. SQL files can also be run in SQLite-compatible tools after loading the CSVs or against the supplied databases (drop existing views before CREATE).

The automated checks use PORTFOLIO_ROOT when provided; otherwise their packaged location determines the root. They validate SQL aggregation, date boundaries, missing answers, leakage and model behaviour.

To refresh the dashboard and case studies after rerunning the analysis:
```
python3 source/src/deliver.py --root .
```
The interactive HTML embeds the generated result JSON and works without a server. A local preview can be served using python3 -m http.server 8765 --bind 127.0.0.1.

## Office files
XLSX formulas recalculate from the supplied analytical inputs. Survey input counts come from the SQL pipeline, not live source connections. To refresh source counts, rerun Python and rebuild the Office files. Deck charts are editable native charts with embedded workbook snapshots; they are not linked to a live database. The Office builder uses the bundled Codex artifact-tool runtime and the selected Simple Dark Mode reference. A conventional Python environment can reproduce the analysis and dashboard independently; Office reauthoring requires that runtime and reference. The optional scripts in source/office accept PORTFOLIO_ROOT (absolute extracted folder), PORTFOLIO_TEMPLATE (reference PPTX), PRESENTATION_SKILL (bundled presentation skill directory), and PORTFOLIO_PYTHON. Node must resolve @oai/artifact-tool; browser checks additionally require Playwright and PORTFOLIO_BROWSER. Run the scripts with PORTFOLIO_ROOT set; they write their previews and validation receipts beside the scripts. package_portfolio.py is the original workspace packaging helper and is not needed to reproduce an extracted portfolio.

## File ownership and provenance
source/ holds the authored pipeline, SQL and verification code. data/ holds exact inputs or documented derived tables. Retention data is synthetic. Stack Overflow survey data and derivatives retain ODbL 1.0 and DbCL 1.0 terms and attribution. No license for Gartner names or logos is implied; no Gartner logo is used.

## Scope of verification
Read quality-report.md and verification/ for executed checks and limitations. Passing tests on synthetic/public data does not establish real business impact or production readiness.
''')
    put(OUT/'interview-guide.md',f'''
# Interview preparation

## Honest ownership
These projects were built with AI assistance at your request. Before claiming a skill, reproduce a result and explain the implementation. A truthful description is: “I used an AI coding assistant to help implement the portfolio, then reviewed the metric definitions, reproduced the SQL results and evaluated the limitations.” Only say the review and reproduction parts after doing them.

## A 90-second retention explanation
“The business problem is prioritising limited outreach before subscription renewal. I used a clearly labelled simulation with {s['historical_clients']:,} historical clients and {s['upcoming_clients']} upcoming renewals. SQL turns event and support histories into features observed 60 days before each renewal. I kept later renewals out of model training and compared a transparent rule with logistic regression. At {s['capacity']['flagged']} contacts, the model identified {s['capacity']['tp']} non-renewals, but that is targeting performance, not customers saved. My proposed next step is a controlled outreach pilot.”

## A 90-second AI explanation
“I analysed the official Stack Overflow 2025 download to understand AI use and trust. The file has {t['respondents']:,} respondents. I separated current from planned usage and used question-specific denominators. Among {t['users_answering_trust']:,} current users who answered trust, {t['low_trust_users']:,} reported distrust, or {pct(t['low_trust_share'])}. I also documented missing data and a discrepancy between the downloaded row count and the published methodology. The findings suggest content experiments, not proof of enterprise buying demand.”

## Questions you should be able to answer

**Why not start with a complex model?**
The decision needs understandable signals and a measurable baseline. Logistic regression is sufficient to demonstrate feature construction, train/test separation and ranking evaluation. Complexity would not make the synthetic evidence more real.

**What is data leakage?**
Using information that would not have been available when the decision was made. Renewal outcome and activity after the cutoff never become inputs. Fitting a scaler on the entire dataset is also leakage; this pipeline fits it on training records only.

**How did you avoid double counting?**
Activity and tickets are both many-to-one relationships with clients. A direct join can multiply rows. SQL aggregates each separately before joining contracts.

**What is precision versus recall?**
Precision is how many flagged accounts actually do not renew. Recall is how many of all non-renewals the flags catch. The rule has {pct(s['rule']['precision'])} precision and {pct(s['rule']['recall'])} recall in the synthetic holdout.

**Why is model precision 100% at threshold 0.5 not a headline?**
It comes from only {s['model']['flagged']} flagged records and misses {s['model']['fn']} non-renewals. Small denominator and very low recall make that headline misleading.

**Why time-based validation?**
The intended workflow uses past outcomes to inform later decisions. A later-period holdout resembles that sequence. One holdout is still limited; real data would need rolling evaluation and monitoring.

**Why not call flagged value money saved?**
An account may renew without intervention, and contact may have no effect. Only an incremental intervention estimate can support a savings or uplift claim.

**Why not fill survey blanks with No?**
Missing answers are not negative answers. That would distort adoption. Report nonresponse and explicitly define which questions people answered.

**Why can frustration percentages exceed 100%?**
Each respondent can choose multiple problems. Count each person once per category and use people answering the question as the denominator.

**Why do your numbers differ from the website?**
The download has 182 more rows than the methodology's retained sample. This project also conditions trust on current users. Both population and denominator can differ. The discrepancy is disclosed and not resolved by inventing exclusions.

**Does the survey show Gartner client demand?**
No. It provides an external developer signal. Testing with the actual intended audience is necessary before inferring demand or allocating material budgets.

**Where are LLMs used?**
AI assisted project implementation. The analysis itself uses SQL, explicit survey categories and an interpretable model. No LLM classified the answers, and no paid LLM service processed data. A future free-text classifier would need human-labelled examples, precision/recall evaluation, privacy review and comparison with a simple baseline.

## Seven-day study plan before October 9
1. Open both dashboards and describe their business decisions without notes.
2. Learn SELECT, GROUP BY, JOIN, CASE and NULLIF using the supplied SQL.
3. Recalculate adoption, precision and recall with a calculator and Excel.
4. Trace a retention client from raw events to its cutoff features.
5. Explain the model features, time split and two false positives.
6. Practise both five-slide presentations, including limitations.
7. Run a mock interview and rewrite every explanation in your own words.

## Self-check exercises with answers
- Ten flagged accounts, four non-renewals, eight total non-renewals: precision 40%, recall 50%.
- 80 current users, 10 planned users, 100 usage answers: current adoption 80%, current-or-planned 90%.
- 20 low-trust current users, 50 current users answering trust, 80 total current users: low-trust share 40%, not 25%.
- Five activity rows and three tickets joined directly for one client: up to 15 rows. Aggregate both facts first.
- Zero previous activity: decline is undefined. Retain NULL for reporting and document any model imputation.
''')
    put(OUT/'resume-bullets.md',f'''
# Portfolio descriptions for your application

Use these only after personally reviewing the work. Keep the AI-assistance disclosure available and answer ownership questions directly. Do not claim employment, real clients or measured uplift.

**Client Retention & Engagement Analytics — SQL, Python, Excel**
- Developed with AI assistance a reproducible subscription-analytics case study covering {s['historical_clients']:,} synthetic historical contracts and {s['activity_events']:,} activity events; used SQL to construct renewal features and an interactive outreach dashboard.
- Evaluated an interpretable logistic model on {s['holdout_n']} later-period contracts, reporting AUC {s['model']['auc']:.2f}, precision/recall and an equal-capacity rule comparison; documented leakage controls and a proposed retention experiment.

**AI Adoption & Trust Intelligence — SQL, Python, Excel**
- Developed with AI assistance an analysis of {t['respondents']:,} public Stack Overflow survey responses, separating current and planned AI usage and documenting nonresponse and source-count discrepancies.
- Built interactive audience comparisons and formula-based Excel reporting; identified that {pct(t['low_trust_share'])} of current users answering trust reported distrust and translated findings into testable content hypotheses.

These projects do not include a Power BI .pbix file. List Power BI only if you separately build and can explain a Power BI implementation. The supplied presentations demonstrate PowerPoint-compatible deliverables, not personal mastery of PowerPoint until you review and edit them.
''')
    put(OUT/'role-alignment.md','''
# Alignment to Gartner requisition 113297

The source for this mapping is the job description supplied by the user in this conversation.

| Role responsibility | Portfolio evidence |
|---|---|
| Client retention and product analytics | Retention SQL model, service engagement, renewal cohorts and outreach queue |
| Statistical analysis and ML | Logistic baseline, temporal holdout, AUC, Brier score, precision/recall; descriptive survey intervals |
| Demand sensing and content | AI trust and frustration analysis; proposed content experiments |
| Data pipelines and large data | Repeatable CSV → validation → SQLite views → analysis exports → dashboards |
| Quality and consistency | Unique-ID checks, reconciled counts, source hashes, time-window and join validation |
| Excel and PowerPoint | Formula-based workbooks, native charts, editable decks and speaker notes |
| Executive communication | Five-slide narratives and decision-oriented case studies |
| LLM exposure | AI-assisted development is disclosed; live LLM analytics integration is not implemented |
| Collaboration | No real stakeholder collaboration is claimed; stakeholder questions and proposed rollout are documented |

## Stakeholder questions for a real deployment
What counts as a meaningful interaction? Is renewal decided before the nominal renewal date? What are the actual outreach cost and capacity? Which customer segments have reliable event coverage? What is the acceptable false-positive workload? Which target audience should validate a content hypothesis?
''')
    wb_inputs={'retention':r,'ai':a}
    (SRC/'.build/workbook-inputs.json').write_text(json.dumps(wb_inputs))
    (OUT/'source').mkdir(exist_ok=True)
    for folder in ['src','sql']:
        if (SRC/folder).resolve() != (OUT/'source'/folder).resolve():
            shutil.copytree(SRC/folder,OUT/'source'/folder,dirs_exist_ok=True)
    print('Dashboards, case studies and learning material generated.')

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path);args=parser.parse_args()
    if args.root:
        OUT=args.root.resolve();SRC=OUT/'source';WORK=OUT
        (SRC/'.build').mkdir(exist_ok=True)
    build()
