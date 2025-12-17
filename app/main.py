from fastapi import FastAPI, HTTPException
from pathlib import Path
from alembic import command
from alembic.config import Config
from .settings import settings
from .db import init_db, fetch_result, sync_selected_leagues
from .tasks import (
    add,
    fetch_fixtures_for_date,
    fetch_recent_fixtures,
    fetch_odds_for_fixture,
    fetch_odds_for_open_selected_fixtures,
)

app = FastAPI(title=settings.APP_NAME)


@app.on_event("startup")
def _startup():
    cfg = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    command.upgrade(cfg, "head")
    init_db()
    sync_selected_leagues()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/tasks/add")
def create_add_task(x: int, y: int):
    task = add.delay(x, y)
    return {"celery_task_id": task.id, "state": task.state}


@app.get("/tasks/{task_id}")
def get_task_result(task_id: str):
    row = fetch_result(task_id)
    if not row:
        return {"celery_task_id": task_id, "db_result": None, "hint": "任务可能还没跑完，或还没写入数据库"}
    return row


@app.post("/tasks/fixtures/day")
def trigger_fetch_fixtures_for_date(day: str):
    t = fetch_fixtures_for_date.delay(day)
    return {"celery_task_id": t.id, "task": "tasks.fetch_fixtures_for_date", "day": day}


@app.post("/tasks/fixtures/recent")
def trigger_fetch_recent_fixtures(days: int = 7):
    t = fetch_recent_fixtures.delay(days)
    return {"celery_task_id": t.id, "task": "tasks.fetch_recent_fixtures", "days": days}


@app.post("/tasks/odds/fixture/{fixture_id}")
def trigger_fetch_odds_for_fixture(fixture_id: int):
    t = fetch_odds_for_fixture.delay(fixture_id)
    return {"celery_task_id": t.id, "task": "tasks.fetch_odds_for_fixture", "fixture_id": fixture_id}


@app.post("/tasks/odds/open-selected")
def trigger_fetch_odds_for_open_selected_fixtures():
    t = fetch_odds_for_open_selected_fixtures.delay()
    return {"celery_task_id": t.id, "task": "tasks.fetch_odds_for_open_selected_fixtures"}
