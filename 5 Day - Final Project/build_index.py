"""
build_index.py — превращает Markdown-корпус (data/corpus.md) в FAISS-индекс.

Шаги:
  1. Читаем data/corpus.md и режем на документы по заголовкам «# Title».
  2. Режем на чанки (CHUNK_SIZE / CHUNK_OVERLAP).
  3. Получаем эмбеддинги через text-1024.
  4. Нормализуем векторы и кладём в FAISS (IndexFlatIP = косинусная близость).
  5. Сохраняем index.faiss + index_meta.json (тексты чанков и их источники).

Свои данные просто дописывай в data/corpus.md (формат: «# Заголовок» /
«Source: <url>» / текст) и перезапускай этот скрипт.

Запуск:  python build_index.py
"""
import json
import os
import re
import time

import numpy as np
import requests
import faiss

import config
import apilog


def load_corpus() -> list[dict]:
    """Парсит data/corpus.md: документы разделены заголовком «# Title».
    Внутри документа необязательная строка «Source: <url>», дальше — текст."""
    raw = open(config.CORPUS_PATH, encoding="utf-8").read()
    # каждый документ начинается с «# » в начале строки
    blocks = re.split(r"(?m)^# ", raw)
    docs = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        lines = block.splitlines()
        title = lines[0].strip()
        source, body_lines = "", []
        for ln in lines[1:]:
            if not body_lines and ln.strip().lower().startswith("source:"):
                source = ln.split(":", 1)[1].strip()
            else:
                body_lines.append(ln)
        body = "\n".join(body_lines).strip()
        if not body:
            continue
        if not source:
            source = "local://corpus.md"
        docs.append({"source": source, "title": title, "text": body})
    return docs


def chunk_text(text: str, size: int, overlap: int) -> list[str]:
    text = text.strip()
    if len(text) <= size:
        return [text] if text else []
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunk = text[start:end]
        chunks.append(chunk.strip())
        start += size - overlap
    return [c for c in chunks if c]


MAX_ATTEMPTS = 7          # больше попыток — переживаем длительный rate-limit
INTER_CALL_DELAY = 0.25   # троттлинг между чанками, чтобы не упираться в 429


def embed_batch(texts: list[str]) -> np.ndarray:
    """Эмбеддинги для списка текстов (поэлементно), устойчиво к 429/5xx."""
    vectors = []
    total = len(texts)
    for n, t in enumerate(texts, 1):
        payload = {"model": config.EMB_MODEL, "input": t}
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.EMB_KEY}",
        }
        for attempt in range(MAX_ATTEMPTS):
            try:
                apilog.request(f"EMBED {n}/{total}", config.EMB_MODEL, t)
                with apilog.timer() as tm:
                    r = requests.post(
                        config.EMB_URL, json=payload, headers=headers,
                        timeout=config.REQUEST_TIMEOUT,
                    )
                # 429/5xx — ждём (учитываем Retry-After) и повторяем
                if r.status_code == 429 or r.status_code >= 500:
                    wait = float(r.headers.get("Retry-After", 0)) or min(3 * 2 ** attempt, 40)
                    apilog.response(f"EMBED {n}/{total}", r.status_code, tm.dt,
                                    f"повтор через {wait:.0f}s ({attempt + 1}/{MAX_ATTEMPTS})")
                    if attempt == MAX_ATTEMPTS - 1:
                        r.raise_for_status()
                    time.sleep(wait)
                    continue
                vec = r.json()["data"][0]["embedding"] if r.ok else None
                apilog.response(f"EMBED {n}/{total}", r.status_code, tm.dt,
                                f"dim={len(vec)}" if vec else (r.text or "")[:120])
                r.raise_for_status()
                vectors.append(vec)
                break
            except requests.exceptions.RequestException as e:
                apilog.error(f"EMBED {n}/{total} попытка {attempt + 1}", e)
                if attempt == MAX_ATTEMPTS - 1:
                    raise RuntimeError(f"Эмбеддинг не получен: {e}")
                time.sleep(min(3 * 2 ** attempt, 40))
        time.sleep(INTER_CALL_DELAY)  # вежливый троттлинг
    arr = np.array(vectors, dtype="float32")
    return arr


def main():
    if not os.path.exists(config.CORPUS_PATH):
        raise SystemExit(
            f"Нет {config.CORPUS_PATH} — сначала запусти: python scrape.py"
        )

    docs = load_corpus()
    if not docs:
        raise SystemExit(
            f"В {config.CORPUS_PATH} нет документов — запусти scrape.py или добавь свои."
        )

    # 1. Чанкинг
    meta = []  # параллельно векторам: {text, source, title}
    for d in docs:
        for ch in chunk_text(d["text"], config.CHUNK_SIZE, config.CHUNK_OVERLAP):
            meta.append({
                "text": ch,
                "source": d["source"],
                "title": d.get("title", ""),
            })
    print(f"Документов: {len(docs)} → чанков: {len(meta)}")

    # 2. Эмбеддинги
    print("Получаю эмбеддинги через text-1024…")
    texts = [m["text"] for m in meta]
    vecs = embed_batch(texts)
    print(f"Векторы: {vecs.shape}")

    if vecs.shape[1] != config.EMB_DIM:
        print(f"  ! Внимание: размерность {vecs.shape[1]} != EMB_DIM {config.EMB_DIM}. "
              f"Поправь EMB_DIM в config.py.")

    # 3. Нормализация → косинус через inner product
    faiss.normalize_L2(vecs)
    index = faiss.IndexFlatIP(vecs.shape[1])
    index.add(vecs)

    # 4. Сохранение
    faiss.write_index(index, config.INDEX_PATH)
    with open(config.META_PATH, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False)

    print(f"\nГотово:")
    print(f"  {config.INDEX_PATH}  ({index.ntotal} векторов)")
    print(f"  {config.META_PATH}")
    print("Следующий шаг: streamlit run app.py")


if __name__ == "__main__":
    main()
