import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.model_selection import cross_val_predict, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.ensemble import HistGradientBoostingClassifier, ExtraTreesClassifier, VotingClassifier
from sklearn.metrics import accuracy_score, f1_score
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
def sc(m):return Pipeline([('i',SimpleImputer(strategy='median')),('s',StandardScaler()),('m',m)])
def im(m):return Pipeline([('i',SimpleImputer(strategy='median')),('m',m)])
v4=VotingClassifier([('svc',sc(SVC(C=30,gamma=0.01,probability=True,random_state=42))),
    ('hgb',HistGradientBoostingClassifier(random_state=42,learning_rate=0.079,max_iter=240,max_leaf_nodes=43,min_samples_leaf=24,l2_regularization=7.26)),
    ('et',im(ExtraTreesClassifier(n_estimators=430,max_features=0.89,min_samples_leaf=1,random_state=42,n_jobs=-1))),
    ('mlp',sc(MLPClassifier(hidden_layer_sizes=(128,64),alpha=1e-3,max_iter=400,early_stopping=True,random_state=42)))],voting='soft',n_jobs=-1)
proba=cross_val_predict(v4,X,y,cv=StratifiedKFold(5,shuffle=True,random_state=42),method='predict_proba',n_jobs=-1)
pred=proba.argmax(1)
P(f"OOF accuracy = {accuracy_score(y,pred):.4f} | macro-F1 = {f1_score(y,pred,average='macro'):.4f}")
# top-2 accuracy: is the true label among top-2 most probable?
top2=np.argsort(-proba,1)[:,:2]
t2=np.mean([y[i] in top2[i] for i in range(len(y))])
P(f"Top-2 accuracy = {t2:.4f}  (если истина почти всегда в топ-2, ошибки = реальное перекрытие 2 классов)")
# confidence vs accuracy
mp=proba.max(1)
for lo,hi in [(0,0.4),(0.4,0.5),(0.5,0.6),(0.6,0.8),(0.8,1.01)]:
    m=(mp>=lo)&(mp<hi)
    if m.sum()>0: P(f"  conf [{lo:.1f},{hi:.1f}): {m.sum():5d} эпох ({m.mean()*100:4.1f}%), accuracy={accuracy_score(y[m],pred[m]):.3f}")
# how often a wrong prediction has true label as 2nd choice
wrong=pred!=y
second=top2[:,1]
P(f"Среди ОШИБОК: доля где истина = 2-й по вероятности класс: {np.mean(second[wrong]==y[wrong]):.3f}")
P("=> высокая доля = ошибки неустранимы (два класса реально неразделимы по этим признакам)")
open(".ceiling_out.txt","w").write("\n".join(log)); print("DONE")
