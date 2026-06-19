"""
scrape.py — сбор данных с сайта фонда Есенова.

Стратегия:
  1. Обходим домен yessenovfoundation.org начиная со стартовых страниц,
     идём только по внутренним ссылкам, ограничены MAX_PAGES.
  2. Из каждой страницы вытаскиваем заголовок + читаемый текст.
  3. Дополнительно добавляем "процедурные карточки" вручную (PROCEDURE_CARDS) —
     это явные ответы на процедурные вопросы со ссылками
     ("где результаты", "как подать заявку"). RAG найдёт их так же,
     как и текст сайта, и отдаст пользователю со ссылкой.

  4. Оставляем только РУССКИЕ версии страниц (ru/en/kk-дубли схлопываются).

Результат: data/corpus.md — все документы в одном файле, каждый в виде:
  # Заголовок
  Source: url

  текст…

Запуск:  python scrape.py
"""
import time
import re
from collections import deque
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

import config


HEADERS = {
    "User-Agent": "YDL2026-student-project/1.0 (educational RAG bot)"
}


def clean_text(html: str) -> tuple[str, str]:
    """Возвращает (title, plain_text), выкидывая мусор."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "svg"]):
        tag.decompose()
    title = (soup.title.string.strip() if soup.title and soup.title.string else "")
    # Собираем видимый текст блоками
    parts = []
    for el in soup.find_all(["h1", "h2", "h3", "h4", "p", "li", "td", "th", "blockquote"]):
        t = el.get_text(" ", strip=True)
        if t and len(t) > 1:
            parts.append(t)
    text = "\n".join(parts)
    # Сжимаем лишние пробелы/переводы строк
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return title, text


def same_domain(url: str, base_netloc: str) -> bool:
    try:
        return urlparse(url).netloc in ("", base_netloc)
    except Exception:
        return False


def crawl() -> list[dict]:
    base_netloc = urlparse(config.BASE_SITE).netloc
    seen = set()
    queue = deque()
    for p in config.SEED_PATHS:
        queue.append(urljoin(config.BASE_SITE, p))

    docs = []
    while queue and len(docs) < config.MAX_PAGES:
        url = queue.popleft()
        url = url.split("#")[0].rstrip("/")
        if not url or url in seen:
            continue
        seen.add(url)
        try:
            r = requests.get(url, headers=HEADERS, timeout=config.REQUEST_TIMEOUT)
            if r.status_code != 200 or "text/html" not in r.headers.get("Content-Type", ""):
                continue
        except Exception as e:
            print(f"  ! пропуск {url}: {e}")
            continue

        title, text = clean_text(r.text)
        if len(text) > 200:  # отбрасываем пустышки
            docs.append({"source": url, "title": title, "text": text})
            print(f"  + [{len(docs)}] {url}  ({len(text)} симв.)")

        # собираем внутренние ссылки
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", href=True):
            nxt = urljoin(url, a["href"]).split("#")[0].rstrip("/")
            if same_domain(nxt, base_netloc) and nxt not in seen:
                # игнорируем файлы
                if not re.search(r"\.(pdf|jpg|jpeg|png|zip|docx?|xlsx?|mp4)$", nxt, re.I):
                    queue.append(nxt)

        time.sleep(config.CRAWL_DELAY)

    return docs


# --- Процедурные карточки: явные ответы со ссылками ---
# Отредактируй ссылки/тексты под реальные данные фонда.
# Именно через них реализован сценарий "где результаты / как получить доступ".
PROCEDURE_CARDS = [
    {
        "source": "manual://procedure/results",
        "title": "Где публикуются результаты по заявке",
        "text": (
            "Результаты рассмотрения заявок на гранты и стипендии фонда Есенова "
            "публикуются на официальном сайте фонда и дополнительно сообщаются "
            "заявителю по электронной почте, указанной в заявке. "
            "Проверить статус и итоги можно на странице: "
            "https://yessenovfoundation.org . "
            "Если результатов ещё нет — значит рассмотрение продолжается; "
            "точные сроки публикации указываются в условиях конкретной программы."
        ),
    },
    {
        "source": "manual://procedure/apply",
        "title": "Как подать заявку",
        "text": (
            "Заявка подаётся через официальный сайт фонда Есенова в разделе "
            "соответствующей программы. Перейдите по ссылке "
            "https://yessenovfoundation.org , выберите программу, "
            "ознакомьтесь с требованиями и заполните форму. "
            "После отправки заявки вы получите подтверждение на email."
        ),
    },
]


def logical_key(source: str) -> str:
    """Ключ страницы без языкового префикса — чтобы схлопнуть ru/en/kk-дубли."""
    if source.startswith("manual://"):
        return source
    path = urlparse(source).path
    return re.sub(r"^/(ru|en|kk)(?=/|$)", "", path) or "/"


def is_russian(text: str) -> bool:
    """Грубое определение: кириллицы больше латиницы и мало казахских букв."""
    head = text[:3000]
    kk = len(re.findall(r"[әқғңұүһіөӘҚҒҢҰҮҺІӨ]", head))
    cyr = len(re.findall(r"[а-яА-Я]", head))
    lat = len(re.findall(r"[a-zA-Z]", head))
    return cyr > lat and kk <= 15


def select_russian(docs: list[dict]) -> list[dict]:
    """Оставляет по одной РУССКОЙ версии каждой логической страницы.
    Страницы без русской версии (только kk/en) отбрасываются."""
    groups: dict[str, list[dict]] = {}
    for d in docs:
        groups.setdefault(logical_key(d["source"]), []).append(d)

    def has_lang_prefix(d):
        return 1 if re.match(r"^/(ru|en|kk)(/|$)", urlparse(d["source"]).path) else 0

    selected, dropped = [], 0
    for items in groups.values():
        ru = [d for d in items if d["source"].startswith("manual://")
              or is_russian(d["text"])]
        if not ru:
            dropped += 1
            continue
        # предпочитаем версию без префикса (она полнее), затем самую длинную
        ru.sort(key=lambda d: (has_lang_prefix(d), -len(d["text"])))
        selected.append(ru[0])
    print(f"Дедуп/фильтр: {len(docs)} → {len(selected)} русских "
          f"(отброшено групп без русской версии: {dropped})")
    return selected


def write_corpus(path: str, docs: list[dict]):
    """Все документы в ОДИН .md: '# Title' + 'Source: url' + текст."""
    with open(path, "w", encoding="utf-8") as f:
        f.write("<!-- Корпус данных бота фонда Есенова (только русский). "
                "Добавляй документы блоком: '# Заголовок' / 'Source: <url>' / текст. -->\n\n")
        for d in docs:
            title = (d.get("title") or "").replace("\n", " ").strip() or "Без названия"
            f.write(f"# {title}\n")
            f.write(f"Source: {d.get('source', '')}\n\n")
            f.write(d.get("text", "").strip() + "\n\n")


def main():
    print("Скрейпинг сайта фонда…")
    docs = crawl()
    print(f"Собрано страниц: {len(docs)}")

    docs.extend(PROCEDURE_CARDS)
    print(f"Добавлено процедурных карточек: {len(PROCEDURE_CARDS)}")

    docs = select_russian(docs)

    import os
    os.makedirs(config.DATA_DIR, exist_ok=True)
    write_corpus(config.CORPUS_PATH, docs)

    print(f"\nГотово → {config.CORPUS_PATH}  ({len(docs)} документов)")
    print("Можешь вручную дописывать свои данные в этот файл (см. README).")
    print("Следующий шаг: python build_index.py")


if __name__ == "__main__":
    main()
