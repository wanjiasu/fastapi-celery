import psycopg2
import json
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .settings import settings


def get_conn():
    return psycopg2.connect(settings.POSTGRES_DSN)


def init_db():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS task_results (
                    id SERIAL PRIMARY KEY,
                    celery_task_id TEXT UNIQUE NOT NULL,
                    result TEXT,
                    created_at TIMESTAMPTZ DEFAULT now()
                );
                """
            )
            conn.commit()


def save_result(celery_task_id: str, result: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO task_results (celery_task_id, result)
                VALUES (%s, %s)
                ON CONFLICT (celery_task_id)
                DO UPDATE SET result = EXCLUDED.result;
                """,
                (celery_task_id, result),
            )
            conn.commit()


def fetch_result(celery_task_id: str):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT celery_task_id, result, created_at FROM task_results WHERE celery_task_id=%s",
                (celery_task_id,),
            )
            return cur.fetchone()

engine = create_engine(
    settings.POSTGRES_DSN,
    pool_pre_ping=True,
    json_serializer=lambda o: json.dumps(o, ensure_ascii=False),
    json_deserializer=lambda s: json.loads(s),
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def sync_selected_leagues():
    raw = getattr(settings, "LEAGUE_IDS", "")
    ids = []
    for s in raw.split(","):
        s = s.strip()
        if s:
            try:
                ids.append(int(s))
            except Exception:
                pass
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("CREATE TABLE IF NOT EXISTS selected_leagues (league_id INT PRIMARY KEY)")
            if ids:
                cur.execute("DELETE FROM selected_leagues WHERE league_id NOT IN (%s)" % ",".join(["%s"] * len(ids)), ids)
                for i in ids:
                    cur.execute("INSERT INTO selected_leagues (league_id) VALUES (%s) ON CONFLICT (league_id) DO NOTHING", (i,))
            conn.commit()
