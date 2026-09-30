import unittest, json, sqlite3, sys, os, tempfile, hashlib
from pathlib import Path
import numpy as np
import pandas as pd

HERE=Path(__file__).resolve()
PACKAGED=HERE.parent.parent.name=='source'
ROOT=Path(os.environ.get('PORTFOLIO_ROOT',HERE.parents[2] if PACKAGED else HERE.parents[2]/'outputs/analyst-portfolio'))
SOURCE=ROOT/'source' if PACKAGED else HERE.parents[2]/'app/analyst-portfolio'
sys.path.insert(0,str(SOURCE/'src'))
from pipeline import wilson,evaluate,feature_matrix,fit_logistic,predict,prepare_survey,auc

class PortfolioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r=json.loads((ROOT/'01-retention/analysis.json').read_text())
        cls.a=json.loads((ROOT/'02-ai-adoption/analysis.json').read_text())
        cls.f=pd.read_csv(ROOT/'01-retention/data/features.csv')
        cls.d=pd.read_csv(ROOT/'02-ai-adoption/data/respondents.csv')

    def test_raw_keys_and_foreign_keys(self):
        base=ROOT/'01-retention/data';clients=pd.read_csv(base/'clients.csv'); ids=set(clients.client_id)
        self.assertFalse(clients.client_id.duplicated().any())
        for table,key in [('contracts','client_id'),('activity','event_id'),('support','ticket_id')]:
            x=pd.read_csv(base/f'{table}.csv');self.assertFalse(x[key].duplicated().any());self.assertTrue(set(x.client_id)<=ids)

    def test_sql_recent_activity_independent(self):
        events=pd.read_csv(ROOT/'01-retention/data/activity.csv')
        z=events.merge(self.f[['client_id','cutoff_date']],on='client_id',validate='many_to_one')
        dates=pd.to_datetime(z.event_date); cutoff=pd.to_datetime(z.cutoff_date)
        actual=z[(dates>cutoff-pd.Timedelta(days=30))&(dates<=cutoff)].groupby('client_id').size()
        expected=self.f.set_index('client_id').recent_activity
        pd.testing.assert_series_equal(actual.reindex(expected.index,fill_value=0),expected,check_names=False)

    def test_sql_support_asof_independent(self):
        tickets=pd.read_csv(ROOT/'01-retention/data/support.csv').merge(self.f[['client_id','cutoff_date']],on='client_id',validate='many_to_one')
        valid=tickets[(tickets.opened_date<=tickets.cutoff_date)&(tickets.resolved_date.isna()|(tickets.resolved_date>tickets.cutoff_date))].groupby('client_id').size()
        expected=self.f.set_index('client_id').open_tickets
        pd.testing.assert_series_equal(valid.reindex(expected.index,fill_value=0),expected,check_names=False)

    def test_date_window_boundaries_and_future_leakage(self):
        db=sqlite3.connect(':memory:')
        pd.DataFrame([['A','Technology','Essential']],columns=['client_id','industry','tier']).to_sql('clients',db,index=False)
        pd.DataFrame([['A','2024-04-01','2025-04-01','2025-01-31',1200,0]],columns=['client_id','start_date','renewal_date','cutoff_date','annual_value_usd','renewed']).to_sql('contracts',db,index=False)
        pd.DataFrame([['1','A','2025-01-01','Research read'],['2','A','2025-01-02','Research read'],['3','A','2025-01-31','Expert session'],['4','A','2025-02-01','Research read']],columns=['event_id','client_id','event_date','service']).to_sql('activity',db,index=False)
        pd.DataFrame([],columns=['ticket_id','client_id','opened_date','resolved_date','category']).to_sql('support',db,index=False)
        db.executescript((SOURCE/'sql/retention.sql').read_text())
        before=pd.read_sql_query('SELECT * FROM features',db)
        self.assertEqual(before.recent_activity.iloc[0],2);self.assertEqual(before.prior_activity.iloc[0],1)
        db.execute("INSERT INTO activity VALUES('future','A','2025-03-01','Expert session')")
        pd.testing.assert_frame_equal(before,pd.read_sql_query('SELECT * FROM features',db));db.close()

    def test_temporal_split_and_unknown_outcomes(self):
        f=self.f;self.assertLess(f[f.cohort=='Training'].renewal_date.max(),f[f.cohort=='Holdout'].renewal_date.min())
        self.assertTrue(f[f.cohort=='Upcoming'].renewed.isna().all())
        self.assertTrue((pd.to_datetime(f.renewal_date)-pd.to_datetime(f.cutoff_date)==pd.Timedelta(days=60)).all())
        self.assertEqual(len(f),f.client_id.nunique())

    def test_no_future_observations_for_upcoming(self):
        future=self.f[self.f.cohort=='Upcoming'][['client_id','cutoff_date']]
        events=pd.read_csv(ROOT/'01-retention/data/activity.csv').merge(future,on='client_id')
        self.assertTrue((events.event_date<=events.cutoff_date).all())

    def test_contract_value_reconciles(self):
        x=self.f[self.f.cohort!='Upcoming'];s=self.r['summary']
        self.assertEqual(x.annual_value_usd.sum(),s['eligible_value_usd'])
        self.assertEqual(x.loc[x.renewed==1,'annual_value_usd'].sum(),s['renewed_value_usd'])
        self.assertAlmostEqual(x.renewed.mean(),s['renewal_rate'])

    def test_evaluation_independently(self):
        x=self.f[self.f.cohort=='Holdout'];e=self.r['summary']['rule']
        self.assertEqual(int(((x.renewed==0)&(x.rule_flag==1)).sum()),e['tp'])
        self.assertEqual(e['tp']+e['fp']+e['fn']+e['tn'],len(x))
        self.assertAlmostEqual(e['precision'],e['tp']/e['flagged'])

    def test_zero_denominators(self):
        e=evaluate([0,0],[0,0]);self.assertIsNone(e['precision']);self.assertIsNone(e['recall'])
        self.assertEqual(wilson(0,0),[None,None]);self.assertIsNone(auc([0,0],[.2,.4]))

    def test_model_uses_training_only_and_no_outcome_feature(self):
        train=self.f[self.f.cohort=='Training'];model=fit_logistic(feature_matrix(train),1-train.renewed.to_numpy())
        np.testing.assert_allclose(model['weights'],self.r['model']['weights'],atol=1e-8)
        changed=train.copy();changed['renewed']=1-changed.renewed
        np.testing.assert_array_equal(feature_matrix(train),feature_matrix(changed))
        p=predict(model,feature_matrix(self.f));self.assertTrue(((p>0)&(p<1)).all())

    def test_ai_sql_denominators_independent(self):
        x=self.d;s=self.a['summary'];self.assertEqual(len(x),s['respondents'])
        self.assertEqual(x.ai_usage.notna().sum(),s['usage_answered'])
        current=x.ai_usage.str.startswith('Yes,',na=False)
        self.assertEqual(current.sum(),s['current_users'])
        valid=x[current&x.trust.notna()]
        self.assertEqual(len(valid),s['users_answering_trust'])
        self.assertEqual(valid.trust.isin(['Somewhat distrust','Highly distrust']).sum(),s['low_trust_users'])
        self.assertAlmostEqual(s['low_trust_share'],s['low_trust_users']/s['users_answering_trust'],places=8)

    def test_cube_reconciles_and_no_average_of_percentages(self):
        cube=pd.DataFrame(self.a['cube']);s=self.a['summary']
        for field,total in [('respondents','respondents'),('usage_answered','usage_answered'),('current_user','current_users'),('trust_answered','users_answering_trust'),('low_trust_user','low_trust_users')]:self.assertEqual(cube[field].sum(),s[total])

    def test_multiple_choice_deduplication(self):
        fr=pd.read_csv(ROOT/'02-ai-adoption/data/frustrations.csv');self.assertFalse(fr.duplicated().any())
        z=fr.merge(self.d[['respondent_id','current_user']],on='respondent_id',validate='many_to_one');z=z[z.current_user==1]
        counts=z.groupby('frustration').respondent_id.nunique().to_dict()
        for row in self.a['frustrations']:
            self.assertEqual(counts[row['frustration']],row['respondents']);self.assertLessEqual(row['respondents'],row['denominator'])

    def test_missingness_and_invalid_categories(self):
        cols=['ResponseId','AISelect','AIAcc','WorkExp','DevType','OrgSize','AIFrustration','Country']
        fixture=pd.DataFrame([[1,None,None,None,None,None,None,None],[2,'No, but I plan to soon','Highly distrust',5,'Student',None,'X;X','India']],columns=cols)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'sample.csv';fixture.to_csv(path,index=False);d,fr,_=prepare_survey(path)
            self.assertEqual(d.current_user.sum(),0);self.assertEqual(d.planned_user.sum(),1);self.assertEqual(len(fr),1)
            self.assertEqual(d.experience_band.iloc[0],'Unknown')
            fixture.loc[1,'ResponseId']=1;fixture.to_csv(path,index=False)
            with self.assertRaisesRegex(ValueError,'duplicate'):prepare_survey(path)
            fixture.loc[1,'ResponseId']=2;fixture.loc[1,'AISelect']='Unexpected';fixture.to_csv(path,index=False)
            with self.assertRaisesRegex(ValueError,'Unmapped'):prepare_survey(path)

    def test_wilson_limits(self):
        lo,hi=wilson(0,10);self.assertAlmostEqual(lo,0);self.assertGreater(hi,0)
        lo,hi=wilson(10,10);self.assertLess(lo,1);self.assertAlmostEqual(hi,1)

if __name__=='__main__':unittest.main()
