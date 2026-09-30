"""Reproducible two-project portfolio. Python 3.11+, numpy, pandas. No paid APIs.

Run from any directory: python src/pipeline.py --root /path/to/portfolio
The default paths use the enclosing GST workspace; only dedicated portfolio paths change.
"""
from __future__ import annotations
import argparse, hashlib, json, math, sqlite3
from datetime import date, timedelta
from pathlib import Path
import numpy as np
import pandas as pd

SEED=113297
FEATURES=['recent_activity','activity_decline_filled','no_expert','open_tickets','activated_30d']

def records(df):
    return json.loads(df.to_json(orient='records'))

def write_json(path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def wilson(k,n):
    if not n: return [None,None]
    z=1.96; p=k/n; den=1+z*z/n
    center=(p+z*z/(2*n))/den
    margin=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return [center-margin,center+margin]

def synthesize(n=1400):
    rng=np.random.default_rng(SEED)
    clients=[]; contracts=[]; activity=[]; support=[]
    eid=0; tid=0
    for i in range(n):
        cid=f'C{i+1:04d}'
        future=i>=1200
        renewal=date(2026,3,1) if future else date(2025,1,1)+timedelta(days=int(rng.integers(0,365)))
        cutoff=renewal-timedelta(days=60); start=renewal-timedelta(days=365)
        tier=str(rng.choice(['Essential','Professional','Enterprise'],p=[.45,.4,.15]))
        industry=str(rng.choice(['Technology','Financial services','Manufacturing','Healthcare','Retail']))
        value={'Essential':1200,'Professional':4800,'Enterprise':15000}[tier]
        clients.append([cid,industry,tier])
        engagement=float(rng.lognormal(0,.55)); disengaging=rng.random()<.28
        activation=rng.random()<.78; unresolved=0; recent=0; prior=0; expert=0
        for day in range(365):
            when=start+timedelta(days=day)
            # Hidden disengagement affects activity and renewal, with independent noise.
            rate=.24*engagement
            if day<30 and not activation: rate=0
            if disengaging and when>cutoff-timedelta(days=30): rate*=.22
            count=int(rng.poisson(rate))
            for _ in range(count):
                eid+=1; service=str(rng.choice(['Research read','Webinar','Expert session'],p=[.83,.13,.04]))
                if not future or when<=cutoff:
                    activity.append([f'E{eid:07d}',cid,when.isoformat(),service])
                if cutoff-timedelta(days=30)<when<=cutoff: recent+=1
                if cutoff-timedelta(days=60)<when<=cutoff-timedelta(days=30): prior+=1
                if cutoff-timedelta(days=60)<when<=cutoff and service=='Expert session': expert+=1
        for _ in range(int(rng.poisson(2.2))):
            tid+=1; opened=start+timedelta(days=int(rng.integers(0,365)))
            resolved=opened+timedelta(days=int(rng.choice([2,5,12,45,90])))
            if rng.random()<.1: resolved=None
            category=str(rng.choice(['Access','Content request','Billing']))
            if not future or opened<=cutoff:
                observed_resolved=resolved if not future or (resolved is not None and resolved<=cutoff) else None
                support.append([f'T{tid:05d}',cid,opened.isoformat(),observed_resolved.isoformat() if observed_resolved else None,category])
            if opened<=cutoff and (resolved is None or resolved>cutoff): unresolved+=1
        # Stochastic simulation, not empirical relationships. No chosen result targets.
        logit=-1.65+1.35*disengaging+.45*(not activation)+.32*unresolved-.065*min(recent,20)-.25*(expert>0)+rng.normal(0,.9)
        churn=rng.random()<1/(1+math.exp(-logit))
        contracts.append([cid,start.isoformat(),renewal.isoformat(),cutoff.isoformat(),value,None if future else int(not churn)])
    return {
        'clients':pd.DataFrame(clients,columns=['client_id','industry','tier']),
        'contracts':pd.DataFrame(contracts,columns=['client_id','start_date','renewal_date','cutoff_date','annual_value_usd','renewed']),
        'activity':pd.DataFrame(activity,columns=['event_id','client_id','event_date','service']),
        'support':pd.DataFrame(support,columns=['ticket_id','client_id','opened_date','resolved_date','category'])}

def feature_matrix(df):
    x=df.copy(); x['activity_decline_filled']=x.activity_decline.fillna(0).clip(-3,1)
    x['no_expert']=(x.expert_sessions==0).astype(int)
    return x[FEATURES].to_numpy(float)

def fit_logistic(X,y):
    """Full-batch L2 logistic regression. Fixed settings; fit on training only."""
    mean=X.mean(axis=0); std=X.std(axis=0); std[std==0]=1
    Z=np.column_stack([np.ones(len(X)),(X-mean)/std]); w=np.zeros(Z.shape[1])
    for _ in range(2500):
        p=1/(1+np.exp(-np.clip(Z@w,-30,30)))
        grad=Z.T@(p-y)/len(y); grad[1:]+=.02*w[1:]
        w-=.08*grad
    return {'mean':mean.tolist(),'std':std.tolist(),'weights':w.tolist(),'features':FEATURES,'l2':.02,'iterations':2500,'learning_rate':.08}

def predict(model,X):
    Z=np.column_stack([np.ones(len(X)),(X-np.array(model['mean']))/np.array(model['std'])])
    return 1/(1+np.exp(-np.clip(Z@np.array(model['weights']),-30,30)))

def evaluate(y,flags):
    y=np.asarray(y,int); flags=np.asarray(flags,int)
    tp=int(((y==1)&(flags==1)).sum()); fp=int(((y==0)&(flags==1)).sum())
    fn=int(((y==1)&(flags==0)).sum()); tn=int(((y==0)&(flags==0)).sum())
    return dict(n=len(y),nonrenewals=int(y.sum()),flagged=int(flags.sum()),tp=tp,fp=fp,fn=fn,tn=tn,
                precision=tp/(tp+fp) if tp+fp else None,recall=tp/(tp+fn) if tp+fn else None,
                baseline=float(y.mean()),precision_interval=wilson(tp,tp+fp))

def auc(y,p):
    pos=np.asarray(p)[np.asarray(y)==1]; neg=np.asarray(p)[np.asarray(y)==0]
    return float(((pos[:,None]>neg).sum()+.5*(pos[:,None]==neg).sum())/(len(pos)*len(neg))) if len(pos) and len(neg) else None

def build_retention(source,out):
    folder=out/'01-retention'; (folder/'data').mkdir(parents=True,exist_ok=True)
    frames=synthesize()
    db=sqlite3.connect(folder/'analysis.sqlite')
    # Drop authored views so reruns are deterministic without touching source tables elsewhere.
    for name in ['features','renewal_by_tier','renewal_by_activation','renewal_by_month','rule_evaluation']:
        db.execute(f'DROP VIEW IF EXISTS {name}')
    for name,df in frames.items():
        df.to_csv(folder/'data'/f'{name}.csv',index=False); df.to_sql(name,db,if_exists='replace',index=False)
    db.executescript((source/'sql/retention.sql').read_text())
    f=pd.read_sql_query('SELECT * FROM features ORDER BY client_id',db)
    train=f[f.cohort=='Training']; test=f[f.cohort=='Holdout']
    model=fit_logistic(feature_matrix(train),1-train.renewed.to_numpy())
    f['model_score']=predict(model,feature_matrix(f)); test=f[f.cohort=='Holdout']
    model_eval=evaluate(1-test.renewed,(test.model_score>=.5).astype(int)); model_eval['auc']=auc(1-test.renewed,test.model_score)
    model_eval['brier']=float(np.mean((test.model_score-(1-test.renewed))**2))
    model_eval['baseline_brier']=float(np.mean(((1-train.renewed).mean()-(1-test.renewed))**2))
    rule_eval=evaluate(1-test.renewed,test.rule_flag)
    # Capacity benchmark: compare equal-sized queues, no holdout tuning.
    k=max(1,round(.2*len(test))); ranked=test.sort_values(['model_score','client_id'],ascending=[False,True])
    top_ids=set(ranked.head(k).client_id)
    capacity_eval=evaluate(1-test.renewed,test.client_id.isin(top_ids).astype(int))
    rule_top_ids=set(test.sort_values(['rule_flag','annual_value_usd','client_id'],ascending=[False,False,True]).head(k).client_id)
    rule_capacity=evaluate(1-test.renewed,test.client_id.isin(rule_top_ids).astype(int))
    hist=f[f.cohort!='Upcoming']; upcoming=f[f.cohort=='Upcoming'].copy()
    upcoming['priority_value']=upcoming.model_score*upcoming.annual_value_usd
    upcoming=upcoming.sort_values(['rule_flag','priority_value','client_id'],ascending=[False,False,True])
    def reason(row):
        r=[]
        if row.recent_activity==0:r.append('No activity in last 30 days')
        if row.open_tickets>=2:r.append('At least two open support requests')
        if row.prior_activity>=5 and row.activity_decline>=.4 and row.expert_sessions==0:r.append('Activity down at least 40%; no expert session')
        return '; '.join(r) if r else 'No rule flag; monitor engagement'
    upcoming['reason']=upcoming.apply(reason,axis=1)
    f.to_csv(folder/'data/features.csv',index=False); upcoming.to_csv(folder/'data/outreach_queue.csv',index=False)
    views={name:records(pd.read_sql_query(f'SELECT * FROM {name}',db)) for name in ['renewal_by_tier','renewal_by_activation','renewal_by_month','rule_evaluation']}
    summary={'clients':len(f),'historical_clients':len(hist),'activity_events':len(frames['activity']),
        'renewal_rate':float(hist.renewed.mean()),'eligible_value_usd':int(hist.annual_value_usd.sum()),
        'renewed_value_usd':int(hist.loc[hist.renewed==1,'annual_value_usd'].sum()),
        'value_renewal_rate':float(hist.loc[hist.renewed==1,'annual_value_usd'].sum()/hist.annual_value_usd.sum()),
        'upcoming_clients':len(upcoming),'flagged_upcoming':int(upcoming.rule_flag.sum()),
        'flagged_contract_value_usd':int(upcoming.loc[upcoming.rule_flag==1,'annual_value_usd'].sum()),
        'training_n':len(train),'holdout_n':len(test),'rule':rule_eval,'model':model_eval,'capacity':capacity_eval,'rule_capacity':rule_capacity,**views}
    report={'source':'Synthetic case study, seed 113297; fictional companies and contracts.','as_of':'2025-12-31','summary':summary,
        'clients':records(f),'queue':records(upcoming),'model':model}
    write_json(folder/'analysis.json',report); write_json(folder/'model.json',model)
    db.close()
    return report

def experience_band(value):
    if pd.isna(value): return 'Unknown'
    if value<=5:return '0–5 years'
    if value<=10:return '6–10 years'
    if value<=20:return '11–20 years'
    return '21+ years'

def prepare_survey(raw):
    required=['ResponseId','AISelect','AIAcc','WorkExp','DevType','OrgSize','AIFrustration','Country']
    x=pd.read_csv(raw,usecols=required)
    if x.ResponseId.isna().any() or x.ResponseId.duplicated().any(): raise ValueError('Missing/duplicate respondent IDs')
    allowed_usage={'Yes, I use AI tools daily','Yes, I use AI tools weekly','Yes, I use AI tools monthly or infrequently',"No, and I don't plan to",'No, but I plan to soon'}
    allowed_trust={'Somewhat trust','Highly trust','Neither trust nor distrust','Somewhat distrust','Highly distrust'}
    if set(x.AISelect.dropna())-allowed_usage: raise ValueError('Unmapped usage category')
    if set(x.AIAcc.dropna())-allowed_trust: raise ValueError('Unmapped trust category')
    d=pd.DataFrame({'respondent_id':x.ResponseId,'ai_usage':x.AISelect,'trust':x.AIAcc,
        'work_experience':x.WorkExp,'experience_band':x.WorkExp.map(experience_band),
        'role':x.DevType.fillna('Unknown'),'organization_size':x.OrgSize.fillna('Unknown'),
        'country':x.Country.fillna('Unknown'),
        'current_user':x.AISelect.str.startswith('Yes,',na=False).astype(int),
        'planned_user':(x.AISelect=='No, but I plan to soon').astype(int),
        'low_trust':x.AIAcc.isin(['Somewhat distrust','Highly distrust']).astype(int),
        'frustration_answered':x.AIFrustration.notna().astype(int)})
    fr=x[['ResponseId','AIFrustration']].dropna().assign(AIFrustration=lambda v:v.AIFrustration.str.split(';')).explode('AIFrustration')
    fr.columns=['respondent_id','frustration']; fr=fr.drop_duplicates()
    return d,fr,x

def build_ai(raw,out):
    folder=out/'02-ai-adoption'; (folder/'data').mkdir(parents=True,exist_ok=True)
    d,fr,x=prepare_survey(raw); db=sqlite3.connect(folder/'analysis.sqlite')
    for name in ['ai_overview','experience_segments','frustration_summary']: db.execute(f'DROP VIEW IF EXISTS {name}')
    d.to_sql('respondents',db,if_exists='replace',index=False); fr.to_sql('frustrations',db,if_exists='replace',index=False)
    source=Path(__file__).resolve().parents[1]
    db.executescript((source/'sql/ai_adoption.sql').read_text())
    summary=records(pd.read_sql_query('SELECT * FROM ai_overview',db))[0]
    segments=pd.read_sql_query('SELECT * FROM experience_segments',db)
    segments['interval_low']=[wilson(k,n)[0] for k,n in zip(segments.low_trust_users,segments.trust_answered)]
    segments['interval_high']=[wilson(k,n)[1] for k,n in zip(segments.low_trust_users,segments.trust_answered)]
    frustrations=pd.read_sql_query('SELECT * FROM frustration_summary',db)
    role_segments=[]
    for role,g in d.groupby('role'):
        valid=g[(g.current_user==1)&g.trust.notna()]
        if len(valid)>=100:
            role_segments.append({'role':role,'trust_answered':len(valid),'low_trust_users':int(valid.low_trust.sum()),'low_trust_share':float(valid.low_trust.mean())})
    roles=pd.DataFrame(role_segments).sort_values('low_trust_share',ascending=False)
    d.to_csv(folder/'data/respondents.csv',index=False); fr.to_csv(folder/'data/frustrations.csv',index=False)
    segments.to_csv(folder/'data/experience_segments.csv',index=False); frustrations.to_csv(folder/'data/frustration_summary.csv',index=False)
    roles.to_csv(folder/'data/role_segments.csv',index=False)
    # Aggregate filter cube is sufficient for dashboard metrics. No individual survey answers in HTML.
    cube=d.assign(usage_answered=d.ai_usage.notna().astype(int),trust_answered=((d.current_user==1)&d.trust.notna()).astype(int),
        low_trust_user=((d.current_user==1)&(d.low_trust==1)).astype(int),respondents=1,
        frustration_denominator=((d.current_user==1)&(d.frustration_answered==1)).astype(int)).groupby(['experience_band','role','organization_size'],as_index=False)[['respondents','usage_answered','current_user','planned_user','trust_answered','low_trust_user','frustration_denominator']].sum()
    fc=fr.merge(d[['respondent_id','experience_band','role','organization_size','current_user']],on='respondent_id',validate='many_to_one')
    fc=fc[fc.current_user==1].groupby(['experience_band','role','organization_size','frustration'],as_index=False).agg(respondents=('respondent_id','nunique'))
    source_info={'publisher':'Stack Overflow','year':2025,'url':'https://survey.stackoverflow.co/2025/',
        'data_url':'https://github.com/StackExchange/Survey/tree/main/packages/archive/2025',
        'methodology_url':'https://survey.stackoverflow.co/2025/methodology',
        'download_url':'https://media.githubusercontent.com/media/StackExchange/Survey/main/packages/archive/2025/results.csv',
        'downloaded_on':'2026-09-30','sha256':sha(raw),'raw_rows':len(d),'published_retained_rows':49009,
        'population_note':'This downloaded public file has 49,191 rows, while the published methodology states 49,009 retained responses. We analyze the downloaded file with explicit question-level denominators, do not invent a missing exclusion rule, and do not claim exact replication of published statistics.',
        'license':'ODbL 1.0 (database); DbCL 1.0 (contents)','license_url':'https://opendatacommons.org/licenses/odbl/1-0/'}
    report={'source':source_info,'summary':summary,'segments':records(segments),'frustrations':records(frustrations),'roles':records(roles),
        'cube':records(cube),'frustration_cube':records(fc),
        'quality':{'duplicate_ids':int(d.respondent_id.duplicated().sum()),'missing_usage':int(d.ai_usage.isna().sum()),
        'missing_trust':int(d.trust.isna().sum()),'missing_work_experience':int(d.work_experience.isna().sum()),
        'usage_missing_rate':float(d.ai_usage.isna().mean()),'raw_row_difference_from_published':len(d)-49009}}
    write_json(folder/'analysis.json',report); write_json(folder/'SOURCE.json',source_info)
    db.close(); return report

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--root',type=Path); args=parser.parse_args()
    source=Path(__file__).resolve().parents[1]
    if args.root:
        out=args.root.resolve(); raw=out/'02-ai-adoption/data/stackoverflow_2025.csv'
    else:
        workspace=source.parents[1]; out=workspace/'outputs/analyst-portfolio'; raw=workspace/'research/analyst-portfolio/raw/stackoverflow_2025.csv'
    out.mkdir(parents=True,exist_ok=True)
    ret=build_retention(source,out); ai=build_ai(raw,out)
    write_json(out/'portfolio_summary.json',{'retention':ret['summary'],'ai':ai['summary']})
    print(json.dumps({'retention':ret['summary'],'ai':ai['summary'],'ai_quality':ai['quality']},indent=2))

if __name__=='__main__':main()
