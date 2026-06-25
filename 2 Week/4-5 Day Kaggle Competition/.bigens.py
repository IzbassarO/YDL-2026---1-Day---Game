import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.model_selection import cross_val_score, cross_val_predict, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.ensemble import HistGradientBoostingClassifier, ExtraTreesClassifier, RandomForestClassifier, VotingClassifier
from sklearn.metrics import f1_score
log=[]; P=lambda s:(log.append(str(s)),print(s,flush=True))
tr=pd.read_csv('train.csv'); feat=[c for c in tr.columns if c not in('id','sleep_stage')]; y=tr.sleep_stage.values
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
X=fe(tr[feat])
def sc(m):return Pipeline([('i',SimpleImputer(strategy='median')),('s',StandardScaler()),('m',m)])
def im(m):return Pipeline([('i',SimpleImputer(strategy='median')),('m',m)])
def M(seed=42):
    return {
    'svc':sc(SVC(C=80,gamma=0.008,probability=True,random_state=seed)),
    'hgb':HistGradientBoostingClassifier(random_state=seed,learning_rate=0.079,max_iter=240,max_leaf_nodes=43,min_samples_leaf=24,l2_regularization=7.26),
    'et':im(ExtraTreesClassifier(n_estimators=430,max_features=0.89,min_samples_leaf=1,random_state=seed,n_jobs=-1)),
    'mlp1':sc(MLPClassifier(hidden_layer_sizes=(128,64),alpha=1e-3,max_iter=400,early_stopping=True,random_state=seed)),
    'rf':im(RandomForestClassifier(n_estimators=500,random_state=seed,n_jobs=-1)),
    'mlp2':sc(MLPClassifier(hidden_layer_sizes=(200,100),activation='tanh',alpha=1e-3,max_iter=400,early_stopping=True,random_state=seed)),
    }
def vote(keys,seed=42):
    md=M(seed); return VotingClassifier([(k,md[k]) for k in keys],voting='soft',n_jobs=-1)
def msc(keys):
    return np.mean([cross_val_score(vote(keys,s),X,y,cv=StratifiedKFold(5,shuffle=True,random_state=s),scoring='f1_macro',n_jobs=-1).mean() for s in [0,1,42]]),\
           np.std([cross_val_score(vote(keys,s),X,y,cv=StratifiedKFold(5,shuffle=True,random_state=s),scoring='f1_macro',n_jobs=-1).mean() for s in [0,1,42]])
sets=[('V4 base',['svc','hgb','et','mlp1']),
      ('V5 +rf',['svc','hgb','et','mlp1','rf']),
      ('V5 +mlp2',['svc','hgb','et','mlp1','mlp2']),
      ('V6 +rf+mlp2',['svc','hgb','et','mlp1','rf','mlp2'])]
best=None
for nm,keys in sets:
    mu,sd=msc(keys); P(f"{nm:14s} macroF1={mu:.4f}±{sd:.4f}")
    if best is None or mu>best[1]: best=(nm,mu,keys)
P(f"\nBest: {best[0]} = {best[1]:.4f}")
oof=cross_val_predict(vote(best[2],42),X,y,cv=StratifiedKFold(5,shuffle=True,random_state=42),n_jobs=-1)
P("per-class F1: "+" ".join(f"{names[i]}={f1_score(y,oof,average=None)[i]:.3f}" for i in range(4)))
open(".bigens_out.txt","w").write("\n".join(log)); print("DONE")
