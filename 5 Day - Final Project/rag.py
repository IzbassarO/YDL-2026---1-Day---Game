"""
rag.py — ядро retrieval-augmented generation.

Главное правило проекта: бот НЕ выдумывает.
  - Ищем top-k чанков.
  - Если лучший score < RELEVANCE_THRESHOLD → возвращаем "не знаю" БЕЗ вызова LLM.
  - Иначе подаём найденный контекст в gemma4 с жёсткой инструкцией
    отвечать только по контексту.
"""
import json
import time

import numpy as np
import requests
import faiss

import config
import apilog


def _short_err(r) -> str:
    """Короткое описание HTTP-ошибки из тела ответа."""
    body = (r.text or "").replace("\n", " ")
    return f"ERR {body[:120]}"


# Дейктические слова → вопрос, скорее всего, follow-up (зависит от предыдущего хода)
_DEICTIC = (
    "он ", "она ", "оно ", "они ", "это", "этот", "эта", "эти", "тот", "та ",
    "туда", "там", "тогда", "его", "её", "их ", "ему", "ей ", "им ",
    "ранее", "раньше", "до этого", "выше", "об этом", "о нём", "о ней",
)
# Признаки вопроса О САМОМ РАЗГОВОРЕ (мета) — отвечаем по истории, без grounding
_META = (
    "что я спрашивал", "что я задавал", "какие вопросы я", "о чём мы",
    "что ты говорил", "что ты отвечал", "ты сказал", "ты говорил", "ты упоминал",
    "повтори", "предыдущ", "ранее я", "до этого ты", "наш разговор", "наша беседа",
    "что я писал",
)


def _is_followup(query: str) -> bool:
    q = " " + query.lower().strip()
    if len(query.split()) <= 4:        # очень короткий вопрос — вероятно, продолжение
        return True
    return any(w in q for w in _DEICTIC)


def _is_meta(query: str) -> bool:
    q = query.lower()
    return any(w in q for w in _META)


def _post_retry(url: str, payload: dict, headers: dict, kind: str, log_text: str,
                max_attempts: int = 4):
    """POST с логом и ретраями на 429/5xx и сетевые сбои (экспон. бэкофф)."""
    for attempt in range(max_attempts):
        apilog.request(kind, payload.get("model", ""), log_text)
        try:
            with apilog.timer() as t:
                r = requests.post(url, json=payload, headers=headers,
                                  timeout=config.REQUEST_TIMEOUT)
        except Exception as e:
            apilog.error(kind, e)
            if attempt == max_attempts - 1:
                raise
            time.sleep(1.5 * (attempt + 1))
            continue
        # 429 / 5xx — временные, повторяем
        if r.status_code == 429 or r.status_code >= 500:
            apilog.response(kind, r.status_code, t.dt,
                            f"повтор {attempt + 1}/{max_attempts}…")
            if attempt == max_attempts - 1:
                return r, t.dt
            time.sleep(2.0 * (attempt + 1))
            continue
        return r, t.dt


SYSTEM_PROMPT = (
    "Ты — дружелюбный официальный ИИ-консультант фонда Шахмардана Есенова. "
    "Веди себя как вежливый помощник, но факты о фонде НЕ выдумывай. Правила:\n"
    "1. ПРИВЕТСТВИЯ, благодарности, прощания, вопросы о тебе и твоих возможностях, "
    "общие любезности — отвечай тепло и естественно, кратко представься и предложи "
    "помощь по темам фонда (YDL, гранты, стипендии, программы, как подать заявку). "
    "Это нормально и НЕ требует материалов.\n"
    "2. ФАКТЫ О ФОНДЕ (программы, YDL, гранты, даты, суммы, требования, имена, ссылки) "
    "бери ТОЛЬКО из блока «МАТЕРИАЛЫ ФОНДА». НЕ выдумывай цифры, даты, условия и имена. "
    "Если материалов по фактическому вопросу нет или их недостаточно — честно скажи: "
    "«В материалах фонда я не нашёл точного ответа на этот вопрос. Уточните, "
    "пожалуйста, на сайте yessenovfoundation.org».\n"
    "3. РАЗГОВОР: на вопросы о самой беседе («что я спрашивал?», «что ты отвечал?») — "
    "отвечай по ИСТОРИИ ДИАЛОГА выше. Если пользователь приписывает тебе слова — "
    "сверься с историей и мягко поправь, если такого не было.\n"
    "4. ВНЕ ТЕМЫ фонда (погода, код, спорт, общие знания, личные советы) — вежливо "
    "откажись: ты консультант фонда и помогаешь только по его темам.\n"
    "5. Если в МАТЕРИАЛАХ есть относящаяся к вопросу ссылка — приведи её. "
    "Отвечай кратко, тепло, по делу, на языке вопроса.\n"
    "6. Представляйся («Я — консультант фонда…») и здоровайся ТОЛЬКО в начале диалога "
    "или если спросили, кто ты. В обычных ответах НЕ повторяй приветствие — сразу к делу."
)


class RAG:
    def __init__(self):
        self.index = faiss.read_index(config.INDEX_PATH)
        with open(config.META_PATH, encoding="utf-8") as f:
            self.meta = json.load(f)

    # --- retrieval ---
    def _embed(self, text: str) -> np.ndarray:
        payload = {"model": config.EMB_MODEL, "input": text}
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.EMB_KEY}",
        }
        r, dt = _post_retry(config.EMB_URL, payload, headers, "EMBED", text)
        emb = r.json()["data"][0]["embedding"] if r.ok else None
        apilog.response("EMBED", r.status_code, dt,
                        f"dim={len(emb)}" if emb else _short_err(r))
        r.raise_for_status()
        vec = np.array([emb], dtype="float32")
        faiss.normalize_L2(vec)
        return vec

    def retrieve(self, query: str, k: int = None):
        k = k or config.TOP_K
        qv = self._embed(query)
        scores, idx = self.index.search(qv, k)
        hits = []
        for score, i in zip(scores[0], idx[0]):
            if i < 0:
                continue
            m = self.meta[i]
            hits.append({"score": float(score), **m})
        return hits

    # --- generation ---
    def _call_gemma(self, messages: list[dict]) -> str:
        payload = {"model": config.CHAT_MODEL, "messages": messages}
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.CHAT_KEY}",
        }
        last = messages[-1]["content"] if messages else ""
        r, dt = _post_retry(config.CHAT_URL, payload, headers, "CHAT", last)
        content = (r.json()["choices"][0]["message"]["content"].strip()
                   if r.ok else None)
        apilog.response("CHAT", r.status_code, dt,
                        f"«{content[:90]}»" if content else _short_err(r))
        r.raise_for_status()
        return content

    def _condense(self, query: str, recent_turns: list[dict]) -> str:
        """Переписывает follow-up в самостоятельный поисковый запрос по истории.
        Один дешёвый вызов LLM. Самодостаточный вопрос вернётся почти как есть."""
        convo = "\n".join(
            f"{'Пользователь' if m['role'] == 'user' else 'Бот'}: {m['content'][:160]}"
            for m in recent_turns[-4:]
        )
        sys_p = (
            "Перепиши ПОСЛЕДНИЙ вопрос пользователя в самостоятельный поисковый запрос "
            "на русском: раскрой местоимения (он/это/туда) и подставь опущенный предмет "
            "из диалога. Верни ТОЛЬКО запрос, без пояснений и кавычек. Если вопрос уже "
            "самостоятельный — верни его без изменений. Если это приветствие, благодарность "
            "или не вопрос — верни текст без изменений."
        )
        usr_p = f"Диалог:\n{convo}\n\nПоследний вопрос: {query}\n\nСамостоятельный запрос:"
        try:
            out = self._call_gemma([
                {"role": "system", "content": sys_p},
                {"role": "user", "content": usr_p},
            ])
            return (out.strip().strip('"') or query)[:300]
        except Exception as e:
            apilog.error("CONDENSE", e)
            return query

    def answer(self, query: str, summary: str = "", recent_turns: list[dict] = None):
        """
        Возвращает dict: {answer, hits, grounded(bool), top_score, source_mode}.
        source_mode: "materials" (по чанкам) | "chat" (по истории) | "general"
        (приветствие/консультация/отказ — без материалов).

        Бот сам решает (по системному промпту): приветствие и лёгкую консультацию
        отвечает естественно; факты о фонде — строго по материалам (иначе «не нашёл»);
        вне темы — вежливо отклоняет. Жёсткого «канонного» отказа без LLM больше нет.

        Память:
          - recent_turns: последние реплики диалога (бот ВИДИТ свои прошлые ответы);
          - summary: «overall»-саммари для долгой памяти (экономит токены);
          - follow-up вопросы переписываются в самостоятельные перед поиском.
        """
        recent_turns = recent_turns or []
        meta = _is_meta(query)
        apilog.step(f"вопрос: «{query[:80]}»"
                    + (" [meta]" if meta else "") + (f" [+{len(recent_turns)} реплик]" if recent_turns else ""))

        # 1) Поиск. Для follow-up переписываем запрос в самостоятельный.
        search_q = query
        if recent_turns and _is_followup(query):
            search_q = self._condense(query, recent_turns)
            if search_q != query:
                apilog.step(f"condense → «{search_q[:80]}»")
        hits = self.retrieve(search_q)
        top_score = hits[0]["score"] if hits else 0.0
        grounded = bool(hits) and top_score >= config.RELEVANCE_THRESHOLD
        mode = "materials" if grounded else ("chat" if meta else "general")
        apilog.step(
            f"retrieve: top_score={top_score:.3f} порог={config.RELEVANCE_THRESHOLD} "
            f"→ режим={mode}"
        )

        # 2) Генерация: системный промпт (+саммари) + последние реплики + блок вопроса.
        sys_content = SYSTEM_PROMPT
        if summary:
            sys_content += (
                "\n\nКРАТКОЕ САММАРИ ПРЕДЫДУЩЕГО ДИАЛОГА (контекст, не источник "
                f"фактов о фонде):\n{summary}"
            )
        messages = [{"role": "system", "content": sys_content}]
        for m in recent_turns[-config.SHORT_MEMORY_TURNS:]:
            messages.append({"role": m["role"], "content": m["content"]})

        if grounded:
            context = "\n\n---\n\n".join(
                f"[Источник: {h['source']}]\n{h['text']}" for h in hits
            )
            user_block = f"МАТЕРИАЛЫ ФОНДА:\n{context}\n\nВОПРОС: {query}"
        elif meta:
            user_block = f"ВОПРОС О НАШЕЙ БЕСЕДЕ: {query}"
        else:
            # подходящих материалов нет: пусть бот сам решит — приветствие/помощь
            # (ответить тепло) или фактический вопрос (честно «не нашёл») / оффтоп (отказ)
            user_block = (
                "Подходящих МАТЕРИАЛОВ ФОНДА по этому сообщению не найдено. "
                "Действуй по правилам: приветствие/благодарность/вопрос о тебе — ответь "
                "тепло; фактический вопрос о фонде — честно скажи, что не нашёл в "
                "материалах; вопрос не по теме фонда — вежливо откажись.\n\n"
                f"СООБЩЕНИЕ ПОЛЬЗОВАТЕЛЯ: {query}"
            )
        messages.append({"role": "user", "content": user_block})

        answer = self._call_gemma(messages)
        return {
            "answer": answer,
            "hits": hits if grounded else [],
            "grounded": grounded,
            "top_score": top_score,
            "source_mode": mode,
        }

    def roll_summary(self, prev_summary: str, user_msg: str, bot_msg: str) -> str:
        """Обновляет скользящее саммари одним дешёвым вызовом LLM.
        Держит его коротким (SUMMARY_MAX_CHARS) — память «в целом», без деталей."""
        apilog.step("обновляю саммари диалога")
        sys_p = (
            "Ты ведёшь КРАТКОЕ саммари диалога пользователя с ботом фонда Есенова. "
            f"Верни обновлённое саммари НЕ длиннее {config.SUMMARY_MAX_CHARS} символов, "
            "2-4 предложения. Сохрани ключевые темы, сущности (например YDL, конкретные "
            "программы/имена) и намерения пользователя. Только сам текст саммари, без преамбул."
        )
        usr_p = (
            f"Текущее саммари:\n{prev_summary or '(пусто)'}\n\n"
            f"Новый вопрос пользователя: {user_msg}\n"
            f"Ответ бота: {bot_msg}\n\n"
            "Обновлённое саммари:"
        )
        try:
            new_sum = self._call_gemma([
                {"role": "system", "content": sys_p},
                {"role": "user", "content": usr_p},
            ])
        except Exception as e:
            apilog.error("SUMMARY", e)
            return prev_summary  # при сбое не теряем старое
        return new_sum[:config.SUMMARY_MAX_CHARS].strip()

    def summarize_dialog(self, history: list[dict]) -> str:
        """Краткое саммари диалога для email администратору."""
        convo = "\n".join(
            f"{'Пользователь' if m['role']=='user' else 'Бот'}: {m['content']}"
            for m in history
        )
        messages = [
            {"role": "system", "content":
                "Сделай краткое деловое саммари диалога пользователя с ботом фонда "
                "(3-5 предложений): что спрашивал пользователь, что важного выяснилось, "
                "есть ли запрос/заявка. Без воды."},
            {"role": "user", "content": convo},
        ]
        return self._call_gemma(messages)
