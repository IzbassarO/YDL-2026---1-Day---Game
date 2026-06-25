import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer, SimpleImputer
from sklearn.model_selection import StratifiedKFold, cross_val_score, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.ensemble import HistGradientBoostingClassifier, ExtraTreesClassifier, VotingClassifier
from sklearn.metrics import f1_score
log=[]; P=lambda s:(log.append(str(s)),print(s,flush=True))
tr=pd.read_csv('train.csv'); te=pd.read_csv('test.csv'); feat=[c for c in tr.columns if c not in('id','sleep_stage')]; y=tr.sleep_stage.values
names={0:'Wake',1:'Light',2:'Deep',3:'REM'}; has=tr.eog_burst_index.notna().values
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
def II(): return IterativeImputer(max_iter=10,random_state=42)
def sc_(m):return Pipeline([('i',II()),('s',StandardScaler()),('m',m)])
def im_(m):return Pipeline([('i',II()),('m',m)])
def v5(seed=42):
    return VotingClassifier([
        ('svc',sc_(SVC(C=80,gamma=0.008,probability=True,random_state=seed))),
        ('hgb',im_(HistGradientBoostingClassifier(random_state=seed,learning_rate=0.079,max_iter=240,max_leaf_nodes=43,min_samples_leaf=24,l2_regularization=7.26))),
        ('et',im_(ExtraTreesClassifier(n_estimators=430,max_features=0.89,min_samples_leaf=1,random_state=seed,n_jobs=-1))),
        ('mlp1',sc_(MLPClassifier(hidden_layer_sizes=(128,64),alpha=1e-3,max_iter=400,early_stopping=True,random_state=seed))),
        ('mlp2',sc_(MLPClassifier(hidden_layer_sizes=(200,100),activation='tanh',alpha=1e-3,max_iter=400,early_stopping=True,random_state=seed)))],
        voting='soft',n_jobs=-1)
# multi-seed confirm
P("Multi-seed confirm (V5 + IterativeImputer):")
scs=[]
for s in [0,1,42]:
    sc=cross_val_score(v5(s),X,y,cv=StratifiedKFold(5,shuffle=True,random_state=s),scoring='f1_macro',n_jobs=-1).mean()
    scs.append(sc); P(f"  seed={s}: {sc:.4f}")
P(f"  MEAN = {np.mean(scs):.4f} ± {np.std(scs):.4f}  (median-imputer was 0.8365)")
# per-class + has/no-eog breakdown
oof=cross_val_predict(v5(42),X,y,cv=StratifiedKFold(5,shuffle=True,random_state=42),n_jobs=-1)
P("per-class F1: "+" ".join(f"{names[i]}={f1_score(y,oof,average=None)[i]:.3f}" for i in range(4)))
P(f"  has-eog={f1_score(y[has],oof[has],average='macro'):.4f}  no-eog={f1_score(y[~has],oof[~has],average='macro'):.4f}  (median was 0.857/0.818)")
# build submission_05 (seed-bagged)
probs=np.zeros((len(Xt),4))
for s in [0,1,42]:
    m=v5(s); m.fit(X,y); probs+=m.predict_proba(Xt)
probs/=3; pred=probs.argmax(1)
sub=pd.DataFrame({'id':te.id,'sleep_stage':pred}); sub.to_csv('submission_05.csv',index=False)
ss=pd.read_csv('sample_submission.csv')
P("Wrote submission_05.csv dist: "+", ".join(f"{names[i]}={(pred==i).mean()*100:.1f}%" for i in range(4)))
P(f"Format OK: {list(sub.columns)==list(ss.columns)} {len(sub)==len(ss)} {(sub.id.values==ss.id.values).all()} {set(sub.sleep_stage)<=set([0,1,2,3])}")
P(f"agree vs submission_04: {(pd.read_csv('submission_04.csv').sleep_stage.values==pred).mean()*100:.1f}%")
open(".sub05_out.txt","w").write("\n".join(log)); print("DONE")
