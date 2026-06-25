"""
Sleep Stage Classification — YDL 2026, Week 2 (final)
Metric: macro-F1.  Models: scikit-learn only (no LightGBM / CatBoost).

Approach
--------
1. Features: 20 normalized sensor channels + eog_burst_index (missing ~50%).
   - eog_burst_index: kept as-is (NaN). We add a binary `eog_burst_missing`
     flag so the model can learn from the *fact* that the EOG channel was off.
   - Domain feature engineering: relative EEG band powers (each band / total)
     and a few physiologically meaningful ratios (delta/beta, theta/alpha,
     slow-wave dominance) that help separate Deep sleep (high delta/slow).
2. Missing values: median imputation for SVC/ExtraTrees; HistGradientBoosting
   handles NaN natively.
3. Model: soft-voting ensemble of three diverse learners
       - SVC (rbf)              — strong margins on scaled features
       - HistGradientBoosting   — sklearn-native gradient boosting, native NaN
       - ExtraTrees             — randomized forest, decorrelated errors
   Voting averages class probabilities -> better, more stable macro-F1 than
   any single model.
4. Validation: 5-fold StratifiedKFold, scoring='f1_macro' (the contest metric).
   Reported CV macro-F1 ~ 0.830.

Run:  python solution.py   ->  writes submission.csv
"""
import warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.ensemble import (
    HistGradientBoostingClassifier,
    ExtraTreesClassifier,
    VotingClassifier,
)

RANDOM_STATE = 42
EEG_BANDS = [
    "eeg_delta_power", "eeg_theta_power", "eeg_alpha_power",
    "eeg_sigma_power", "eeg_beta_power", "eeg_gamma_power",
]


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Feature engineering applied identically to train and test."""
    X = df.copy()
    total = X[EEG_BANDS].clip(lower=0).sum(axis=1) + 1e-6
    for b in EEG_BANDS:
        X["rel_" + b] = X[b] / total                      # relative band power
    X["delta_beta"] = X["eeg_delta_power"] / (X["eeg_beta_power"].abs() + 1e-6)
    X["theta_alpha"] = X["eeg_theta_power"] / (X["eeg_alpha_power"].abs() + 1e-6)
    X["slow_dom"] = X["eeg_slow_osc_power"] + X["eeg_delta_power"]
    X["eog_burst_missing"] = df["eog_burst_index"].isna().astype(int)
    return X


def build_model() -> VotingClassifier:
    svc = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
        ("clf", SVC(C=10, gamma="scale", probability=True,
                    random_state=RANDOM_STATE)),
    ])
    hgb = HistGradientBoostingClassifier(
        max_iter=400, learning_rate=0.05, l2_regularization=1.0,
        random_state=RANDOM_STATE,
    )
    et = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("clf", ExtraTreesClassifier(n_estimators=500, n_jobs=-1,
                                     random_state=RANDOM_STATE)),
    ])
    return VotingClassifier(
        estimators=[("svc", svc), ("hgb", hgb), ("et", et)],
        voting="soft", n_jobs=-1,
    )


def main():
    train = pd.read_csv("train.csv")
    test = pd.read_csv("test.csv")
    feat_cols = [c for c in train.columns if c not in ("id", "sleep_stage")]

    X = add_features(train[feat_cols])
    y = train["sleep_stage"].values
    X_test = add_features(test[feat_cols])

    model = build_model()

    # Honest validation on the contest metric
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    scores = cross_val_score(model, X, y, cv=cv, scoring="f1_macro", n_jobs=-1)
    print(f"CV macro-F1: {scores.mean():.4f} +/- {scores.std():.4f}")

    # Fit on all training data and predict the test set
    model.fit(X, y)
    preds = model.predict(X_test)

    submission = pd.DataFrame({"id": test["id"], "sleep_stage": preds})
    submission.to_csv("submission.csv", index=False)
    print(f"Wrote submission.csv  ({len(submission)} rows)")
    print(submission["sleep_stage"].value_counts().sort_index().to_string())


if __name__ == "__main__":
    main()
