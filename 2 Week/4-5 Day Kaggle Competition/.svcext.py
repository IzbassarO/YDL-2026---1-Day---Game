import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.model_selection import GridSearchCV, cross_val_score, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
log=[]; P=lambda s:(log.append(str(s)),print(s,flush=True))
tr=pd.read_csv('train.csv'); feat=[c for c in tr.columns if c not in('id','sleep_stage')]; y=tr.sleep_stage.values
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
cv42=StratifiedKFold(5,shuffle=True,random_state=42)
pipe=Pipeline([('i',SimpleImputer(strategy='median')),('s',StandardScaler()),('m',SVC(random_state=42))])
grid={'m__C':[20,30,50,80,120,200],'m__gamma':[0.003,0.005,0.008,0.01,0.015,0.02]}
gs=GridSearchCV(pipe,grid,scoring='f1_macro',cv=cv42,n_jobs=-1)
gs.fit(X,y)
P(f"Extended SVC best f1_macro = {gs.best_score_:.4f}  params={gs.best_params_}")
tbl=pd.DataFrame(gs.cv_results_).pivot_table(index='param_m__C',columns='param_m__gamma',values='mean_test_score')
P("Grid (rows=C, cols=gamma):\n"+tbl.round(4).to_string())
# multi-seed confirm best SVC vs old SVC
best=gs.best_params_
def msc(m):
    return np.mean([cross_val_score(m,X,y,cv=StratifiedKFold(5,shuffle=True,random_state=s),scoring='f1_macro',n_jobs=-1).mean() for s in [0,1,42]])
old=Pipeline([('i',SimpleImputer(strategy='median')),('s',StandardScaler()),('m',SVC(C=30,gamma=0.01,random_state=42))])
new=Pipeline([('i',SimpleImputer(strategy='median')),('s',StandardScaler()),('m',SVC(C=best['m__C'],gamma=best['m__gamma'],random_state=42))])
P(f"\nMulti-seed: old SVC(C=30,g=0.01)={msc(old):.4f}  new SVC(C={best['m__C']},g={best['m__gamma']})={msc(new):.4f}")
open(".svcext_out.txt","w").write("\n".join(log)); print("DONE")
