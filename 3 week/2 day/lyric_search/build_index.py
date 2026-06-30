"""Build the two search indexes over lyric lines: tf-idf and IDF-weighted GloVe.

tf-idf  = bag of words: matches on the *words* you typed.
GloVe   = weighted average of word vectors: matches on *meaning*.

Key quality trick (SIF-style): when averaging word vectors we weight each word by
its idf, so frequent fillers ("the", "and", "i") barely count and the content words
("heartbroken", "ocean") dominate the line's meaning vector. Plain averaging lets
stop-words wash the signal out; idf-weighting fixes that. Still Day-2 only.
"""
import re
import json
import pickle
import numpy as np
import pandas as pd
import gensim.downloader as api
from sklearn.feature_extraction.text import TfidfVectorizer

TOK = re.compile(r"[a-z']+")
lines = pd.read_parquet("data/lines.parquet")
texts = lines["line"].tolist()
print(f"indexing {len(texts):,} lines")

# --- tf-idf index (keyword search) ---
tfidf = TfidfVectorizer(stop_words="english", min_df=2)
tfidf_matrix = tfidf.fit_transform(texts)
print(f"tf-idf vocab: {len(tfidf.vocabulary_):,}")

# --- per-word idf over the whole corpus (weights for the meaning vector) ---
widf = TfidfVectorizer(token_pattern=r"(?u)[a-z']+")  # no stop-word removal here
widf.fit(texts)
word_idf = {w: float(widf.idf_[j]) for w, j in widf.vocabulary_.items()}
default_w = float(np.median(list(word_idf.values())))   # weight for unseen query words
json.dump({"idf": {w: round(v, 3) for w, v in word_idf.items()}, "default": round(default_w, 3)},
          open("data/word_idf.json", "w"))
print(f"word-idf weights: {len(word_idf):,}  (default {default_w:.2f})")

# --- IDF-weighted GloVe index (meaning search) ---
print("loading GloVe...")
wv = api.load("glove-wiki-gigaword-100")


def embed(text):
    """idf-weighted average of the GloVe vectors of the words in `text`."""
    num = np.zeros(wv.vector_size, dtype=np.float32)
    den = 0.0
    for w in TOK.findall(text.lower()):
        if w in wv:
            wt = word_idf.get(w, default_w)
            num += wt * wv[w]
            den += wt
    if den == 0:
        return np.zeros(wv.vector_size, dtype=np.float32)
    return num / den


glove_matrix = np.vstack([embed(t) for t in texts]).astype(np.float32)

# SIF step 2 (Arora et al. 2017): remove the top principal component — the
# "common-discourse" direction every line shares. Subtracting it sharpens the
# part that actually distinguishes lines, which improves semantic search.
from sklearn.decomposition import TruncatedSVD
pc = TruncatedSVD(n_components=1, random_state=42).fit(glove_matrix).components_[0].astype(np.float32)
glove_matrix -= (glove_matrix @ pc)[:, None] * pc[None, :]
np.save("data/sif_pc.npy", pc)

norms = np.linalg.norm(glove_matrix, axis=1, keepdims=True)
glove_matrix /= np.clip(norms, 1e-9, None)
print(f"GloVe line matrix: {glove_matrix.shape}  (SIF common component removed)")

with open("data/tfidf.pkl", "wb") as f:
    pickle.dump({"vectorizer": tfidf, "matrix": tfidf_matrix}, f)
np.save("data/glove_lines.npy", glove_matrix)
print("saved -> data/tfidf.pkl, data/glove_lines.npy, data/word_idf.json, data/sif_pc.npy")
