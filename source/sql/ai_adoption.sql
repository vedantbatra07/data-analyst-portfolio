-- Grain: one respondent. Missing answers remain NULL, never 'No'.
-- Low trust: somewhat/highly distrust among CURRENT users answering trust.
CREATE VIEW ai_overview AS
 SELECT COUNT(*) AS respondents,COUNT(ai_usage) AS usage_answered,
 SUM(current_user) AS current_users,SUM(planned_user) AS planned_users,
 SUM(CASE WHEN current_user=1 AND trust IS NOT NULL THEN 1 ELSE 0 END) AS users_answering_trust,
 SUM(CASE WHEN current_user=1 AND low_trust=1 THEN 1 ELSE 0 END) AS low_trust_users,
 1.0*SUM(current_user)/NULLIF(COUNT(ai_usage),0) AS current_adoption,
 1.0*SUM(CASE WHEN current_user=1 AND low_trust=1 THEN 1 ELSE 0 END)/
 NULLIF(SUM(CASE WHEN current_user=1 AND trust IS NOT NULL THEN 1 ELSE 0 END),0) AS low_trust_share
 FROM respondents;

CREATE VIEW experience_segments AS
 SELECT experience_band,COUNT(*) AS respondents,COUNT(ai_usage) AS usage_answered,
 SUM(current_user) AS current_users,
 SUM(CASE WHEN current_user=1 AND trust IS NOT NULL THEN 1 ELSE 0 END) AS trust_answered,
 SUM(CASE WHEN current_user=1 AND low_trust=1 THEN 1 ELSE 0 END) AS low_trust_users,
 1.0*SUM(current_user)/NULLIF(COUNT(ai_usage),0) AS adoption_rate,
 1.0*SUM(CASE WHEN current_user=1 AND low_trust=1 THEN 1 ELSE 0 END)/
 NULLIF(SUM(CASE WHEN current_user=1 AND trust IS NOT NULL THEN 1 ELSE 0 END),0) AS low_trust_share
 FROM respondents GROUP BY experience_band ORDER BY CASE experience_band
 WHEN '0–5 years' THEN 1 WHEN '6–10 years' THEN 2 WHEN '11–20 years' THEN 3
 WHEN '21+ years' THEN 4 ELSE 5 END;

-- Multiple choice: each person contributes at most once to each problem.
-- The denominator is unique CURRENT users who answered the frustration question.
CREATE VIEW frustration_summary AS
 SELECT f.frustration,COUNT(DISTINCT f.respondent_id) AS respondents,
 (SELECT COUNT(*) FROM respondents WHERE current_user=1 AND frustration_answered=1) AS denominator,
 1.0*COUNT(DISTINCT f.respondent_id)/NULLIF((SELECT COUNT(*) FROM respondents WHERE current_user=1 AND frustration_answered=1),0) AS share
 FROM frustrations f JOIN respondents r USING(respondent_id)
 WHERE r.current_user=1 GROUP BY f.frustration ORDER BY respondents DESC;
