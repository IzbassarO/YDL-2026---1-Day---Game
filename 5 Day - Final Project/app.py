"""
app.py — Streamlit-чат по грантам фонда Есенова (RAG на gemma4).

Главное: бот отвечает ТОЛЬКО по данным с сайта фонда. Если в индексе нет
релевантного — честно говорит «не знаю» (см. rag.py, RELEVANCE_THRESHOLD).

Запуск:  streamlit run app.py
"""
import time

import streamlit as st

import config
from rag import RAG
import email_report
import db


st.set_page_config(page_title="Грант-бот фонда Есенова", page_icon="🎓")


@st.cache_resource(show_spinner="Загружаю индекс фонда…")
def get_rag():
    return RAG()


def init_state():
    ss = st.session_state
    ss.setdefault("messages", [])        # [{role, content, meta?}]
    ss.setdefault("user_msg_count", 0)   # сообщений пользователя за сессию
    ss.setdefault("last_request_ts", 0.0)
    ss.setdefault("email_status", None)
    ss.setdefault("summary", "")         # скользящее саммари диалога (память)
    ss.setdefault("session_id", None)    # id сессии в Postgres
    ss.setdefault("db_ok", False)
    ss.setdefault("db_error", "")
    # один раз за сессию: поднять схему и создать запись сессии
    if not ss.get("db_init_tried"):
        ss.db_init_tried = True
        try:
            db.init_db()
            ss.session_id = db.create_session()
            ss.db_ok = True
        except Exception as e:
            ss.db_ok = False
            ss.db_error = f"{type(e).__name__}: {e}"


def persist(role: str, content: str, grounded=None, top_score=None):
    """Сохранить сообщение в Postgres (если БД доступна)."""
    ss = st.session_state
    if ss.db_ok and ss.session_id:
        try:
            db.add_message(ss.session_id, role, content, grounded, top_score)
        except Exception as e:
            ss.db_ok = False
            ss.db_error = f"{type(e).__name__}: {e}"


def render_sources(meta: dict):
    """Раскрывающийся блок «Источники» — ключевой элемент демо (честность)."""
    hits = meta.get("hits", [])
    if not hits:
        return
    with st.expander(f"📎 Источники ({len(hits)}) · top score {meta.get('top_score', 0):.3f}"):
        for h in hits:
            src = h.get("source", "")
            title = h.get("title") or src
            score = h.get("score", 0.0)
            snippet = (h.get("text", "")[:300] + "…") if h.get("text") else ""
            if src.startswith("http"):
                st.markdown(f"**[{title}]({src})** · `score {score:.3f}`")
            else:
                st.markdown(f"**{title}** · `{src}` · `score {score:.3f}`")
            st.caption(snippet)


def render_status(meta: dict):
    """Бейдж режима ответа: материалы / по истории диалога / отказ."""
    mode = meta.get("source_mode")
    if mode == "materials" or (mode is None and meta.get("grounded")):
        st.caption("✅ Ответ на основе материалов фонда")
    elif mode == "chat":
        st.caption("💬 Ответ по истории нашего диалога (не из материалов фонда)")
    else:
        st.caption("⚠️ Не найдено в материалах фонда — бот не выдумывает")


def render_message(m: dict):
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        meta = m.get("meta")
        if meta:
            render_status(meta)
            render_sources(meta)


# ---------------------------------------------------------------- UI
init_state()

st.title("🎓 Грант-бот фонда Шахмардана Есенова")
st.caption(
    "Отвечаю на вопросы о грантах, программах и деятельности фонда — "
    "**только** по данным сайта yessenovfoundation.org. "
    "Чего не знаю — честно скажу «не знаю»."
)

# Готовые примеры вопросов — показываем до начала диалога
EXAMPLES_ON = [
    "Что такое Yessenov Data Lab?",
    "Кто такой Шахмардан Есенов?",
    "Как подать заявку на грант?",
    "Кто входит в попечительский совет фонда?",
]
EXAMPLES_OFF = [
    "Какая завтра погода в Алматы?",
    "Напиши код сортировки на Python",
    "Кто выиграл чемпионат мира по футболу?",
]

if not st.session_state.messages:
    st.info(
        "**О чём можно спросить:** Yessenov Data Lab (YDL), фонд Есенова и его миссия, "
        "Шахмардан Есенов, руководство, стипендии и гранты, истории успеха, как подать заявку."
    )
    st.markdown("**✅ Примеры по теме фонда** — нажми, чтобы спросить:")
    cols = st.columns(2)
    for i, q in enumerate(EXAMPLES_ON):
        if cols[i % 2].button(q, key=f"ex_on_{i}", use_container_width=True):
            st.session_state.pending_example = q
    st.markdown("**🚫 А это бот честно отклонит** (вне темы фонда):")
    cols2 = st.columns(3)
    for i, q in enumerate(EXAMPLES_OFF):
        if cols2[i % 3].button(q, key=f"ex_off_{i}", use_container_width=True):
            st.session_state.pending_example = q

# --- Сайдбар: лимиты + email ---
with st.sidebar:
    st.header("О боте")
    st.markdown(
        "- Модель: **gemma4**\n"
        "- Поиск: **RAG / FAISS** по сайту фонда\n"
        "- Память: **скользящее саммари**\n"
        "- Если данных нет — отвечаю «не знаю»"
    )
    used = st.session_state.user_msg_count
    st.progress(min(used / config.MAX_MESSAGES_PER_SESSION, 1.0),
                text=f"Сообщений: {used}/{config.MAX_MESSAGES_PER_SESSION}")

    if st.session_state.db_ok:
        st.caption(f"🟢 Postgres · сессия #{st.session_state.session_id}")
    else:
        st.caption("🟡 Postgres недоступен — история только в этой сессии")
        if st.session_state.db_error:
            st.caption(f"`{st.session_state.db_error}`")
    if st.session_state.summary:
        with st.expander("🧠 Память диалога (саммари)"):
            st.write(st.session_state.summary)

    st.divider()
    st.subheader("📧 Отчёт администратору")
    st.caption(f"Саммари диалога уйдёт на {config.ADMIN_EMAIL}")
    if st.button("Отправить саммари администратору", use_container_width=True,
                 disabled=not st.session_state.messages):
        try:
            rag = get_rag()
            with st.spinner("Готовлю саммари и отправляю…"):
                summary = rag.summarize_dialog(st.session_state.messages)
                msg_id = email_report.send_summary(summary)
            st.session_state.email_status = ("ok", msg_id, summary)
        except Exception as e:
            st.session_state.email_status = ("err", str(e), None)

    es = st.session_state.email_status
    if es:
        if es[0] == "ok":
            st.success(f"Отправлено ✅ message_id: {es[1]}")
            with st.expander("Текст саммари"):
                st.write(es[2])
        else:
            st.error(f"Ошибка отправки: {es[1]}")

# --- История чата ---
for m in st.session_state.messages:
    render_message(m)

# --- Ввод с лимитами ---
limit_reached = st.session_state.user_msg_count >= config.MAX_MESSAGES_PER_SESSION
prompt = st.chat_input(
    "Спросите про гранты, стипендии, программы фонда…",
    disabled=limit_reached,
)
# вопрос, выбранный кнопкой-примером
if not prompt and not limit_reached:
    prompt = st.session_state.pop("pending_example", None)
if limit_reached:
    st.warning(
        f"Достигнут лимит сообщений за сессию "
        f"({config.MAX_MESSAGES_PER_SESSION}). Перезапустите сессию."
    )

if prompt:
    # анти-спам пауза
    now = time.time()
    wait = config.MIN_SECONDS_BETWEEN - (now - st.session_state.last_request_ts)
    if wait > 0:
        st.toast(f"Слишком часто — подождите {wait:.1f} с")
    else:
        st.session_state.last_request_ts = now
        st.session_state.user_msg_count += 1
        st.session_state.messages.append({"role": "user", "content": prompt})
        render_message({"role": "user", "content": prompt})
        persist("user", prompt)

        with st.chat_message("assistant"):
            with st.spinner("Ищу в материалах фонда…"):
                try:
                    rag = get_rag()
                    # память: скользящее саммари + последние реплики (бот видит
                    # свои прошлые ответы); current msg исключаем — он уже в prompt
                    recent = [
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.messages[:-1]
                    ]
                    result = rag.answer(prompt, summary=st.session_state.summary,
                                        recent_turns=recent)
                except Exception as e:
                    err = (
                        "⚠️ Не удалось получить ответ (проблема сети или сервиса "
                        f"alem.ai). Попробуйте ещё раз.\n\n`{type(e).__name__}: {e}`"
                    )
                    st.markdown(err)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": err}
                    )
                    persist("assistant", err)
                    st.stop()

            st.markdown(result["answer"])
            render_status(result)
            render_sources(result)

        st.session_state.messages.append({
            "role": "assistant",
            "content": result["answer"],
            "meta": {
                "grounded": result["grounded"],
                "top_score": result["top_score"],
                "hits": result["hits"],
                "source_mode": result.get("source_mode"),
            },
        })
        persist("assistant", result["answer"],
                result["grounded"], result["top_score"])

        # обновляем скользящее саммари (память) — только на содержательных ответах,
        # чтобы не тратить вызов LLM на «не знаю»
        if result["grounded"]:
            try:
                new_sum = rag.roll_summary(
                    st.session_state.summary, prompt, result["answer"]
                )
                st.session_state.summary = new_sum
                if st.session_state.db_ok and st.session_state.session_id:
                    db.set_summary(st.session_state.session_id, new_sum)
            except Exception:
                pass  # память не критична для ответа
