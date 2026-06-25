import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import SimpleImputer, IterativeImputer, KNNImputer
from sklearn.model_selection import StratifiedKFold, cross_val_score, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.ensemble import HistGradientBoostingClassifier, ExtraTreesClassifier, VotingClassifier
from sklearn.metrics import f1_score
log=[]; P=lambda s:(log.append(str(s)),print(s,flush=True))
tr=pd.read_csv('train.csv'); te=pd.read_csv('test.csv'); feat=[c for c in tr.columns if c not in('id','sleep_stage')]; y=tr.sleep_stage.values
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
# How well can we predict eog_burst_index from other features? (R2)
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import cross_val_score as cvs
hasm=tr.eog_burst_index.notna().values
Xr=X[hasm].drop(columns=['eog_burst_index','eog_burst_missing']).fillna(X.median())
yr=tr.eog_burst_index[hasm].values
r2=cvs(HistGradientBoostingRegressor(random_state=42),Xr,yr,cv=5,scoring='r2').mean()
P(f"Предсказуемость eog_burst_index из др. признаков: R2={r2:.3f} (низкий R2 => импутация не восстановит сигнал)")

def sc_(m,imp):return Pipeline([('i',imp),('s',StandardScaler()),('m',m)])
def im_(m,imp):return Pipeline([('i',imp),('m',m)])
def v5(imp_factory):
    return VotingClassifier([
        ('svc',sc_(SVC(C=80,gamma=0.008,probability=True,random_state=42),imp_factory())),
        ('hgb',Pipeline([('i',imp_factory()),('m',HistGradientBoostingClassifier(random_state=42,learning_rate=0.079,max_iter=240,max_leaf_nodes=43,min_samples_leaf=24,l2_regularization=7.26))])),
        ('et',im_(ExtraTreesClassifier(n_estimators=430,max_features=0.89,min_samples_leaf=1,random_state=42,n_jobs=-1),imp_factory())),
        ('mlp1',sc_(MLPClassifier(hidden_layer_sizes=(128,64),alpha=1e-3,max_iter=400,early_stopping=True,random_state=42),imp_factory())),
        ('mlp2',sc_(MLPClassifier(hidden_layer_sizes=(200,100),activation='tanh',alpha=1e-3,max_iter=400,early_stopping=True,random_state=42),imp_factory()))],
        voting='soft',n_jobs=-1)
cv=StratifiedKFold(5,shuffle=True,random_state=42)
for nm,fac in [('median',lambda:SimpleImputer(strategy='median')),
               ('KNN',lambda:KNNImputer(n_neighbors=10)),
               ('Iterative',lambda:IterativeImputer(max_iter=10,random_state=42))]:
    s=cross_val_score(v5(fac),X,y,cv=cv,scoring='f1_macro',n_jobs=-1).mean()
    P(f"  imputer={nm:10s} V5 f1_macro={s:.4f}")
open(".impute_out.txt","w").write("\n".join(log)); print("DONE")
