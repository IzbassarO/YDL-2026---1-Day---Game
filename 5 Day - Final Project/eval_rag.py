"""
eval_rag.py — системная ТЕМАТИЧЕСКАЯ проверка бота фонда Есенова.

Идея: вопросов бесконечно много, поэтому проверяем не отдельные формулировки,
а ТЕМЫ. Для каждой темы — несколько разных вопросов; смотрим, насколько уверенно
RAG находит контекст (top_score) по теме в целом.

  IN-SCOPE темы  (про фонд/YDL/гранты) → ожидаем высокий score, бот отвечает.
  OUT-OF-SCOPE темы (общие знания, код…) → ожидаем низкий score, бот отказывает.

Выдаёт:
  • карту покрытия по темам (🟢 покрыта / 🟡 частично / 🔴 нет данных),
  • разделимость in/out и рекомендуемый RELEVANCE_THRESHOLD,
  • (опц.) реальные ответы gemma4 и (опц.) отправку email-саммари.

Запуск:
  python eval_rag.py            # тематическая RAG-проверка (быстро, без gemma4)
  python eval_rag.py --full     # + реальные ответы gemma4 по 1 вопросу на тему
  python eval_rag.py --email    # + реально отправит тестовое письмо себе
"""
import sys
import statistics as stats

import config
from rag import RAG


# --- IN-SCOPE: темы про фонд, по каждой — разные формулировки вопросов ---
THEMES_IN = {
    "Yessenov Data Lab (YDL)": [
        "Что такое Yessenov Data Lab?",
        "Расскажи про YDL 2026",
        "Чему учат на Yessenov Data Lab?",
        "Кто может участвовать в YDL?",
    ],
    "Фонд Есенова: миссия и деятельность": [
        "Чем занимается фонд Есенова?",
        "Какая миссия у фонда?",
        "Какие программы есть у фонда?",
        "Что делает фонд Шахмардана Есенова?",
    ],
    "Шахмардан Есенов (личность)": [
        "Кто такой Шахмардан Есенов?",
        "Биография Шахмардана Есенова",
        "Чем известен Шахмардан Есенов?",
    ],
    "Руководство фонда (попечители, эксперты)": [
        "Кто входит в попечительский совет фонда?",
        "Кто такой Галимжан Есенов?",
        "Кто в экспертном совете фонда?",
    ],
    "Стипендии и гранты": [
        "Какие стипендии есть у фонда?",
        "Как получить грант фонда Есенова?",
        "Какие гранты выдаёт фонд?",
    ],
    "Истории успеха выпускников": [
        "Расскажи про выпускников фонда",
        "Истории успеха участников программ",
        "Что стало с выпускниками YDL?",
    ],
    "Процедуры: заявка и результаты": [
        "Как подать заявку?",
        "Где публикуются результаты по заявке?",
        "Как узнать статус моей заявки?",
    ],
}

# --- OUT-OF-SCOPE: темы вне компетенции бота ---
THEMES_OUT = {
    "Общие знания": [
        "Какая столица Франции?",
        "Сколько планет в Солнечной системе?",
        "Когда началась Вторая мировая война?",
    ],
    "Программирование": [
        "Напиши функцию сортировки на Python",
        "Как развернуть строку в JavaScript?",
    ],
    "Быт / погода / цены": [
        "Какая завтра погода в Алматы?",
        "Сколько стоит последний iPhone?",
        "Посоветуй рецепт борща",
    ],
    "Развлечения / спорт": [
        "Кто выиграл чемпионат мира по футболу?",
        "Посоветуй фильм на вечер",
    ],
}


def score_theme(rag, queries):
    """Возвращает (scores_list) — top_score по каждому вопросу темы."""
    out = []
    for q in queries:
        hits = rag.retrieve(q)
        top = hits[0]["score"] if hits else 0.0
        best_src = hits[0]["source"] if hits else "-"
        out.append((q, top, best_src))
    return out


def verdict_in(mean, thr):
    if mean >= thr:
        return "🟢 покрыта"
    if mean >= thr * 0.7:
        return "🟡 частично"
    return "🔴 нет данных"


def run(rag, themes, kind, thr, full):
    print(f"\n{'='*72}\n{kind}\n{'='*72}")
    all_scores = []
    per_theme = {}
    for theme, queries in themes.items():
        rows = score_theme(rag, queries)
        scores = [r[1] for r in rows]
        per_theme[theme] = scores
        all_scores += scores
        mean, mx, mn = stats.mean(scores), max(scores), min(scores)
        if kind.startswith("IN"):
            tag = verdict_in(mean, thr)
        else:
            # для out-of-scope хорошо, когда даже максимум ниже порога
            tag = "🟢 отказ" if mx < thr else "🔴 ложн.ответ"
        print(f"\n▸ {theme}")
        print(f"    среднее={mean:.3f}  макс={mx:.3f}  мин={mn:.3f}   {tag}")
        for q, top, src in rows:
            flag = "✓" if top >= thr else "·"
            print(f"      [{flag} {top:.3f}] {q}")
            if top >= thr:
                print(f"               ↳ {src[:62]}")
        if full and kind.startswith("IN"):
            # один реальный ответ gemma4 на первый вопрос темы
            q0 = queries[0]
            res = rag.answer(q0)
            ans = res["answer"][:200].replace("\n", " ")
            print(f"    gemma4 «{q0}» → {ans}")
    return all_scores, per_theme


def main():
    full = "--full" in sys.argv
    do_email = "--email" in sys.argv
    thr = config.RELEVANCE_THRESHOLD

    print("Загружаю индекс…")
    rag = RAG()
    print(f"Чанков в индексе: {rag.index.ntotal}")
    print(f"RELEVANCE_THRESHOLD = {thr}")

    in_all, in_pt = run(rag, THEMES_IN, "IN-SCOPE (бот должен отвечать)", thr, full)
    out_all, out_pt = run(rag, THEMES_OUT, "OUT-OF-SCOPE (бот должен отказать)", thr, full)

    # --- Сводка ---
    print(f"\n{'='*72}\nСВОДКА ПО ТЕМАМ\n{'='*72}")
    covered = sum(1 for s in in_pt.values() if stats.mean(s) >= thr)
    print(f"IN-SCOPE тем покрыто:  {covered}/{len(in_pt)}")
    bad_out = sum(1 for s in out_pt.values() if max(s) >= thr)
    print(f"OUT-OF-SCOPE тем с ложным ответом: {bad_out}/{len(out_pt)}")

    # --- Калибровка порога по разделимости ---
    # берём медиану in-scope (устойчивее к выбросам) и максимум out-scope
    in_med = stats.median(in_all)
    in_lo = min(in_all)
    out_hi = max(out_all)
    out_p90 = sorted(out_all)[int(len(out_all) * 0.9) - 1]
    print(f"\n{'='*72}\nКАЛИБРОВКА ПОРОГА\n{'='*72}")
    print(f"  IN-SCOPE:  медиана={in_med:.3f}  минимум={in_lo:.3f}")
    print(f"  OUT:       максимум={out_hi:.3f}  p90={out_p90:.3f}")
    if in_lo > out_hi:
        sug = round((in_lo + out_hi) / 2, 3)
        print(f"  ✅ Группы полностью разделимы → RELEVANCE_THRESHOLD ≈ {sug}")
    else:
        # компромисс: чуть выше p90 «чужих», но ниже медианы «своих»
        sug = round((out_p90 + in_med) / 2, 3)
        print(f"  ⚠️ Есть пересечение (in_min={in_lo:.3f} ≤ out_max={out_hi:.3f}).")
        print(f"     Компромиссный порог между p90(out) и медианой(in) ≈ {sug}")
        print(f"     (часть слабых in-scope вопросов уйдёт в «не знаю» — это честнее, "
              f"чем выдумывать)")

    # --- Email ---
    if do_email:
        import email_report
        print(f"\n{'='*72}\nEMAIL-ТЕСТ\n{'='*72}")
        demo = [
            {"role": "user", "content": "Здравствуйте! Что такое Yessenov Data Lab?"},
            {"role": "assistant", "content": "Это программа фонда Есенова по data science."},
            {"role": "user", "content": "Хочу подать заявку, оставьте мой запрос."},
        ]
        try:
            summary = rag.summarize_dialog(demo)
            print("Саммари:\n ", summary.replace("\n", "\n  "))
            mid = email_report.send_summary(summary)
            print(f"\n✅ Отправлено на {config.ADMIN_EMAIL}; message_id: {mid}")
        except Exception as e:
            print(f"\n❌ Ошибка отправки: {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
