import json
from datetime import datetime, timezone
import requests
from pathlib import Path
from sqlalchemy import select
from .celery_app import celery
from .db import save_result, SessionLocal
from .models import League, Fixture, SelectedFixture, OddsQuote
from data_fetcher.leagues import import_leagues_data
from data_fetcher.fixtures import fetch_fixtures_for_date_data
from data_fetcher.odds import fetch_odds_for_fixture_data


@celery.task(name="tasks.add")
def add(x: int, y: int):
    res = x + y
    # 记录到外部 PostgreSQL
    save_result(celery_task_id=add.request.id, result=str(res))
    return res


@celery.task(name="tasks.import_leagues")
def import_leagues():
    res = import_leagues_data()
    req_id = getattr(import_leagues.request, "id", None) or "import-leagues-local"
    save_result(celery_task_id=req_id, result=json.dumps(res))
    return res


@celery.task(name="tasks.fetch_fixtures_for_date")
def fetch_fixtures_for_date(day: str):
    res = fetch_fixtures_for_date_data(day)
    req_id = getattr(fetch_fixtures_for_date.request, "id", None) or f"fixtures-{day}"
    out = {"day": day, **res}
    save_result(celery_task_id=req_id, result=json.dumps(out))
    return out


@celery.task(name="tasks.fetch_recent_fixtures")
def fetch_recent_fixtures(days: int = 7):
    from datetime import datetime, timedelta, timezone
    today = datetime.now(timezone.utc).date()
    scheduled = []
    for i in range(days):
        day = (today - timedelta(days=i)).isoformat()
        t = fetch_fixtures_for_date.delay(day)
        scheduled.append({"day": day, "task_id": t.id})
    req_id = getattr(fetch_recent_fixtures.request, "id", None) or "fixtures-7days"
    save_result(celery_task_id=req_id, result=json.dumps({"scheduled": scheduled}))
    return {"scheduled": scheduled}


@celery.task(name="tasks.fetch_odds_for_fixture")
def fetch_odds_for_fixture(fixture_id: int):
    from .settings import settings
    with SessionLocal() as session:
        sf = session.execute(select(SelectedFixture).where(SelectedFixture.fixture_id == fixture_id)).scalar_one_or_none()
        now_utc = datetime.now(timezone.utc)
        if (not sf) or ((sf.status_long or "") == "Match Finished") or (sf.match_date is None) or (sf.match_date <= now_utc):
            req_id = getattr(fetch_odds_for_fixture.request, "id", None) or f"odds-{fixture_id}"
            save_result(celery_task_id=req_id, result=json.dumps({"fixture_id": fixture_id, "skipped": True}))
            return {"fixture_id": fixture_id, "skipped": True}

    bets_raw = getattr(settings, "BETS_IDS", "")
    bet_ids = set()
    for s in bets_raw.split(","):
        s = s.strip()
        if s:
            try:
                bet_ids.add(int(s))
            except Exception:
                pass
    res = fetch_odds_for_fixture_data(fixture_id, bet_ids)
    req_id = getattr(fetch_odds_for_fixture.request, "id", None) or f"odds-{fixture_id}"
    out = {"fixture_id": fixture_id, **res}
    save_result(celery_task_id=req_id, result=json.dumps(out))
    return out


@celery.task(name="tasks.fetch_odds_for_open_selected_fixtures")
def fetch_odds_for_open_selected_fixtures():
    scheduled = []
    with SessionLocal() as session:
        now_utc = datetime.now(timezone.utc)
        rows = session.execute(
            select(SelectedFixture.fixture_id).where(
                ((SelectedFixture.status_long != "Match Finished") | (SelectedFixture.status_long.is_(None)))
                & (SelectedFixture.match_date > now_utc)
            )
        ).scalars().all()
        for fid in rows:
            t = fetch_odds_for_fixture.delay(int(fid))
            scheduled.append({"fixture_id": int(fid), "task_id": t.id})
    req_id = getattr(fetch_odds_for_open_selected_fixtures.request, "id", None) or "odds-open-fixtures"
    save_result(celery_task_id=req_id, result=json.dumps({"scheduled": scheduled}))
    return {"scheduled": scheduled}
