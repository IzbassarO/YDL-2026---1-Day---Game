import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.ensemble import HistGradientBoostingClassifier, ExtraTreesClassifier, VotingClassifier
tr=pd.read_csv('train.csv'); te=pd.read_csv('test.csv')
feat=[c for c in tr.columns if c not in('id','sleep_stage')]; y=tr.sleep_stage.values
names={0:'Wake',1:'Light',2:'Deep',3:'REM'}
EEG=['eeg_delta_power','eeg_theta_power','eeg_alpha_power','eeg_sigma_power','eeg_beta_power','eeg_gamma_power']
def fe(df):
    X=df.copy(); tot=X[EEG].clip(lower=0).sum(1)+1e-6
    for b in EEG: X['rel_'+b]=X[b]/tot
    X['delta_beta']=X['eeg_delta_power']/(X['eeg_beta_power'].abs()+1e-6)
    X['theta_alpha']=X['eeg_theta_power']/(X['eeg_alpha_power'].abs()+1e-6)
    X['slow_dom']=X['eeg_slow_osc_power']+X['eeg_delta_power']
    X['eog_burst_missing']=df['eog_burst_index'].isna().astype(int)
    return X
X=fe(tr[feat]); Xt=fe(te[feat])
def sc(m):return Pipeline([('i',SimpleImputer(strategy='median')),('s',StandardScaler()),('m',m)])
def im(m):return Pipeline([('i',SimpleImputer(strategy='median')),('m',m)])
def v5(seed):
    return VotingClassifier([
        ('svc',sc(SVC(C=80,gamma=0.008,probability=True,random_state=seed))),
        ('hgb',HistGradientBoostingClassifier(random_state=seed,learning_rate=0.079,max_iter=240,max_leaf_nodes=43,min_samples_leaf=24,l2_regularization=7.26)),
        ('et',im(ExtraTreesClassifier(n_estimators=430,max_features=0.89,min_samples_leaf=1,random_state=seed,n_jobs=-1))),
        ('mlp1',sc(MLPClassifier(hidden_layer_sizes=(128,64),alpha=1e-3,max_iter=400,early_stopping=True,random_state=seed))),
        ('mlp2',sc(MLPClassifier(hidden_layer_sizes=(200,100),activation='tanh',alpha=1e-3,max_iter=400,early_stopping=True,random_state=seed)))],
        voting='soft',n_jobs=-1)
probs=np.zeros((len(Xt),4))
for s in [0,1,42]:
    m=v5(s); m.fit(X,y); probs+=m.predict_proba(Xt)
probs/=3; pred=probs.argmax(1)
sub=pd.DataFrame({'id':te.id,'sleep_stage':pred}); sub.to_csv('submission_04.csv',index=False)
ss=pd.read_csv('sample_submission.csv')
print("Wrote submission_04.csv dist:", ", ".join(f"{names[i]}={(pred==i).mean()*100:.1f}%" for i in range(4)))
print("Format OK:", list(sub.columns)==list(ss.columns), len(sub)==len(ss), (sub.id.values==ss.id.values).all(), set(sub.sleep_stage)<=set([0,1,2,3]))
for prev in ['submission.csv','submission_robust.csv','submission_03.csv']:
    p=pd.read_csv(prev); print(f"agree vs {prev}: {(p.sleep_stage.values==pred).mean()*100:.1f}%")
print("DONE")
