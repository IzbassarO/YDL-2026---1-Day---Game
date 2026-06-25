import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.model_selection import StratifiedKFold, cross_val_score, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import HistGradientBoostingClassifier, ExtraTreesClassifier, VotingClassifier
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

# ---------- 1. RULE HUNT: shallow tree accuracy (any near-deterministic structure?) ----------
P("1. RULE HUNT")
for d in [1,2,3,5]:
    sc_=cross_val_score(im(DecisionTreeClassifier(max_depth=d,random_state=42)),X,y,cv=StratifiedKFold(5,shuffle=True,random_state=42),scoring='f1_macro',n_jobs=-1).mean()
    P(f"   DecisionTree depth={d}: f1_macro={sc_:.4f}")
# single best feature stump purity
from sklearn.feature_selection import f_classif
Xi=X.fillna(X.median())
best=None
for c in feat:
    v=Xi[c].values
    for q in np.quantile(v,[.2,.3,.4,.5,.6,.7,.8]):
        for cls in range(4):
            mask=v>q
            if mask.sum()>50:
                pur=(y[mask]==cls).mean()
                if best is None or pur>best[0]: best=(pur,c,q,cls,'>',mask.sum())
            mask=v<=q
            if mask.sum()>50:
                pur=(y[mask]==cls).mean()
                if best is None or pur>best[0]: best=(pur,c,q,cls,'<=',mask.sum())
P(f"   Лучшее одно-правило: {best[1]} {best[4]} {best[2]:.3f} -> {names[best[3]]} чистота={best[0]:.3f} (n={best[5]})  (0.25=случайно, >0.9=структура)")

# ---------- 2. eog_burst_index PRESENCE ROUTING ----------
P("\n2. ROUTING by eog_burst_index presence (две спец-модели vs единая)")
has=tr.eog_burst_index.notna().values
P(f"   has eog: {has.sum()} ({has.mean()*100:.0f}%) | no eog: {(~has).sum()}")
def v5(seed=42, drop_eog=False):
    cols_drop=['eog_burst_index'] if drop_eog else []
    base=[
        ('svc',sc(SVC(C=80,gamma=0.008,probability=True,random_state=seed))),
        ('hgb',HistGradientBoostingClassifier(random_state=seed,learning_rate=0.079,max_iter=240,max_leaf_nodes=43,min_samples_leaf=24,l2_regularization=7.26)),
        ('et',im(ExtraTreesClassifier(n_estimators=430,max_features=0.89,min_samples_leaf=1,random_state=seed,n_jobs=-1))),
        ('mlp1',sc(MLPClassifier(hidden_layer_sizes=(128,64),alpha=1e-3,max_iter=400,early_stopping=True,random_state=seed))),
        ('mlp2',sc(MLPClassifier(hidden_layer_sizes=(200,100),activation='tanh',alpha=1e-3,max_iter=400,early_stopping=True,random_state=seed)))]
    return VotingClassifier(base,voting='soft',n_jobs=-1)
cv=StratifiedKFold(5,shuffle=True,random_state=42)
# single model OOF
oof_single=cross_val_predict(v5(42),X,y,cv=cv,n_jobs=-1)
# routed OOF: within each fold train two submodels
oof_route=np.zeros(len(y),dtype=int)
for trn,tst in cv.split(X,y):
    for grp in [True,False]:
        tr_idx=trn[has[trn]==grp]; ts_idx=tst[has[tst]==grp]
        if len(ts_idx)==0: continue
        cols=[c for c in X.columns if not (grp==False and c=='eog_burst_index')]
        m=v5(42); m.fit(X.iloc[tr_idx][cols],y[tr_idx])
        oof_route[ts_idx]=m.predict(X.iloc[ts_idx][cols])
P(f"   Single V5  OOF macroF1 = {f1_score(y,oof_single,average='macro'):.4f}")
P(f"   Routed V5  OOF macroF1 = {f1_score(y,oof_route,average='macro'):.4f}")
# breakdown on has-eog subset
for grp,nm in [(True,'has-eog'),(False,'no-eog')]:
    msk=has==grp
    P(f"     [{nm}] single={f1_score(y[msk],oof_single[msk],average='macro'):.4f}  routed={f1_score(y[msk],oof_route[msk],average='macro'):.4f}")
open(".hunt_out.txt","w").write("\n".join(log)); print("DONE")
