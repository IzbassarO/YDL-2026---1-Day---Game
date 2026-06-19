"""
apilog.py — единый лог API-запросов в CLI.

Печатает в stderr: исходящий запрос, статус-код + время ответа, краткий ответ
и ошибки. Виден в терминале, где запущен скрипт/Streamlit, в веб-UI не попадает.

Выключается через переменную окружения:  YDL_LOG_API=0
"""
import sys
import time

import config

# ANSI-цвета (если вывод не в терминал — без них)
_TTY = sys.stderr.isatty()
_CYAN = "\033[36m" if _TTY else ""
_GREEN = "\033[32m" if _TTY else ""
_RED = "\033[31m" if _TTY else ""
_GREY = "\033[90m" if _TTY else ""
_RST = "\033[0m" if _TTY else ""


def _short(s, n: int = 90) -> str:
    s = str(s).replace("\n", " ")
    return s if len(s) <= n else s[:n] + "…"


def request(kind: str, model: str, content: str):
    """Лог исходящего запроса."""
    if not config.LOG_API:
        return
    print(f"{_CYAN}[API →]{_RST} {kind} model={model}  «{_short(content)}»",
          file=sys.stderr, flush=True)


def response(kind: str, status: int, elapsed: float, summary: str = ""):
    """Лог ответа: статус-код, время, краткое содержимое."""
    if not config.LOG_API:
        return
    color = _GREEN if 200 <= status < 300 else _RED
    print(f"{color}[API ←]{_RST} {kind} {status} {_GREY}{elapsed:.2f}s{_RST}  {summary}",
          file=sys.stderr, flush=True)


def error(kind: str, err: Exception):
    """Лог сетевой/прочей ошибки запроса."""
    if not config.LOG_API:
        return
    print(f"{_RED}[API ✗]{_RST} {kind} {type(err).__name__}: {_short(err, 140)}",
          file=sys.stderr, flush=True)


def step(msg: str):
    """Лог шага обработки (например, решение RAG по порогу)."""
    if not config.LOG_API:
        return
    print(f"{_GREY}[RAG]{_RST} {msg}", file=sys.stderr, flush=True)


class timer:
    """Контекст для замера времени запроса: with apilog.timer() as t: ... t.dt"""
    def __enter__(self):
        self._t0 = time.time()
        self.dt = 0.0
        return self

    def __exit__(self, *exc):
        self.dt = time.time() - self._t0
        return False
