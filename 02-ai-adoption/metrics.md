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
