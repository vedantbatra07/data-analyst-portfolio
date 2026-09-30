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
