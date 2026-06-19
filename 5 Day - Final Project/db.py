"""
db.py — хранение истории чата в PostgreSQL.

Таблицы:
  sessions(id, created_at, summary)        — диалоги; summary = скользящее саммари
  messages(id, session_id, role, content,  — сообщения
           grounded, top_score, created_at)

Подключение: DATABASE_URL или PG* из config (по умолчанию локальный Homebrew-postgres).
Все операции обёрнуты так, чтобы приложение не падало, если БД недоступна
(вызывающий код проверяет healthcheck() и при недоступности работает только в памяти).
"""
import psycopg2
import psycopg2.extras

import config
import apilog


_conn = None


def _connect():
    if config.DATABASE_URL:
        return psycopg2.connect(config.DATABASE_URL)
    return psycopg2.connect(
        host=config.PG_HOST, port=config.PG_PORT, dbname=config.PG_DB,
        user=config.PG_USER, password=config.PG_PASSWORD or None,
    )


def conn():
    """Кэшированное соединение с автокоммитом; переподключается, если оборвалось."""
    global _conn
    if _conn is None or _conn.closed:
        _conn = _connect()
        _conn.autocommit = True
    return _conn


SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id          BIGSERIAL PRIMARY KEY,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    summary     TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS messages (
    id          BIGSERIAL PRIMARY KEY,
    session_id  BIGINT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role        TEXT NOT NULL,
    content     TEXT NOT NULL,
    grounded    BOOLEAN,
    top_score   REAL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_messages_session ON messages (session_id, id);
"""


def init_db():
    """Создаёт таблицы, если их нет."""
    with conn().cursor() as cur:
        cur.execute(SCHEMA)


def healthcheck() -> bool:
    """True, если БД доступна (без исключения)."""
    try:
        with conn().cursor() as cur:
            cur.execute("SELECT 1")
        return True
    except Exception as e:
        apilog.error("DB", e)
        return False


def create_session() -> int:
    with conn().cursor() as cur:
        cur.execute("INSERT INTO sessions DEFAULT VALUES RETURNING id")
        return cur.fetchone()[0]


def add_message(session_id: int, role: str, content: str,
                grounded: bool = None, top_score: float = None) -> int:
    with conn().cursor() as cur:
        cur.execute(
            "INSERT INTO messages (session_id, role, content, grounded, top_score) "
            "VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (session_id, role, content, grounded, top_score),
        )
        return cur.fetchone()[0]


def get_messages(session_id: int) -> list[dict]:
    with conn().cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            "SELECT role, content, grounded, top_score, created_at "
            "FROM messages WHERE session_id = %s ORDER BY id",
            (session_id,),
        )
        return [dict(r) for r in cur.fetchall()]


def get_summary(session_id: int) -> str:
    with conn().cursor() as cur:
        cur.execute("SELECT summary FROM sessions WHERE id = %s", (session_id,))
        row = cur.fetchone()
        return row[0] if row else ""


def set_summary(session_id: int, summary: str):
    with conn().cursor() as cur:
        cur.execute("UPDATE sessions SET summary = %s WHERE id = %s",
                    (summary, session_id))


def recent_sessions(limit: int = 10) -> list[dict]:
    """Для отладки/демо: последние сессии с числом сообщений."""
    with conn().cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            "SELECT s.id, s.created_at, s.summary, "
            "       count(m.id) AS n_messages "
            "FROM sessions s LEFT JOIN messages m ON m.session_id = s.id "
            "GROUP BY s.id ORDER BY s.id DESC LIMIT %s",
            (limit,),
        )
        return [dict(r) for r in cur.fetchall()]
