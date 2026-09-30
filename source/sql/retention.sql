-- Grain: one contract/client. Each snapshot is 60 days before renewal.
-- Aggregate fact tables BEFORE joining to avoid activity x ticket fan-out.
CREATE VIEW features AS
WITH activity_features AS (
 SELECT c.client_id,
 SUM(CASE WHEN a.event_date > date(c.cutoff_date,'-30 day') AND a.event_date <= c.cutoff_date THEN 1 ELSE 0 END) AS recent_activity,
 SUM(CASE WHEN a.event_date > date(c.cutoff_date,'-60 day') AND a.event_date <= date(c.cutoff_date,'-30 day') THEN 1 ELSE 0 END) AS prior_activity,
 SUM(CASE WHEN a.event_date > date(c.cutoff_date,'-60 day') AND a.event_date <= c.cutoff_date AND a.service='Expert session' THEN 1 ELSE 0 END) AS expert_sessions,
 COUNT(DISTINCT CASE WHEN a.event_date > date(c.cutoff_date,'-60 day') AND a.event_date <= c.cutoff_date THEN a.service END) AS service_breadth,
 MAX(CASE WHEN a.event_date >= c.start_date AND a.event_date < date(c.start_date,'+30 day') AND a.event_date <= c.cutoff_date THEN 1 ELSE 0 END) AS activated_30d
 FROM contracts c LEFT JOIN activity a ON a.client_id=c.client_id GROUP BY c.client_id
), support_features AS (
 SELECT c.client_id,
 SUM(CASE WHEN t.opened_date <= c.cutoff_date AND (t.resolved_date IS NULL OR t.resolved_date > c.cutoff_date) THEN 1 ELSE 0 END) AS open_tickets
 FROM contracts c LEFT JOIN support t ON c.client_id=t.client_id GROUP BY c.client_id
), joined AS (
 SELECT c.*, cl.industry, cl.tier, a.*, s.open_tickets,
 CASE WHEN a.prior_activity=0 THEN NULL ELSE 1.0-1.0*a.recent_activity/a.prior_activity END AS activity_decline,
 CASE WHEN c.renewal_date<'2025-09-01' THEN 'Training'
      WHEN c.renewal_date<='2025-12-31' THEN 'Holdout' ELSE 'Upcoming' END AS cohort
 FROM contracts c JOIN clients cl USING(client_id)
 JOIN activity_features a USING(client_id) JOIN support_features s USING(client_id)
)
SELECT client_id,start_date,renewal_date,cutoff_date,annual_value_usd,renewed,industry,tier,
 recent_activity,prior_activity,expert_sessions,service_breadth,activated_30d,open_tickets,
 activity_decline,cohort,
 CASE WHEN recent_activity=0 OR open_tickets>=2 OR
 (prior_activity>=5 AND activity_decline>=0.4 AND expert_sessions=0) THEN 1 ELSE 0 END AS rule_flag
FROM joined;

CREATE VIEW renewal_by_tier AS
 SELECT tier,COUNT(*) AS contracts,SUM(renewed) AS renewed_contracts,
 1.0*SUM(renewed)/COUNT(*) AS renewal_rate,
 SUM(annual_value_usd) AS eligible_value_usd,
 SUM(CASE WHEN renewed=1 THEN annual_value_usd ELSE 0 END) AS renewed_value_usd
 FROM features WHERE cohort<>'Upcoming' GROUP BY tier;

CREATE VIEW renewal_by_activation AS
 SELECT activated_30d,COUNT(*) AS contracts,SUM(renewed) AS renewed_contracts,
 1.0*SUM(renewed)/COUNT(*) AS renewal_rate
 FROM features WHERE cohort<>'Upcoming' GROUP BY activated_30d;

CREATE VIEW renewal_by_month AS
 SELECT substr(renewal_date,1,7) AS month,COUNT(*) AS contracts,SUM(renewed) AS renewed_contracts,
 1.0*SUM(renewed)/COUNT(*) AS renewal_rate
 FROM features WHERE cohort<>'Upcoming' GROUP BY month;

CREATE VIEW rule_evaluation AS
 SELECT cohort,COUNT(*) AS clients,SUM(1-renewed) AS nonrenewals,
 SUM(rule_flag) AS flagged,SUM(CASE WHEN rule_flag=1 AND renewed=0 THEN 1 ELSE 0 END) AS true_positives,
 SUM(CASE WHEN rule_flag=1 AND renewed=1 THEN 1 ELSE 0 END) AS false_positives,
 SUM(CASE WHEN rule_flag=0 AND renewed=0 THEN 1 ELSE 0 END) AS false_negatives
 FROM features WHERE cohort<>'Upcoming' GROUP BY cohort;
