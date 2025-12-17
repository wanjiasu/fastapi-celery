import json
from datetime import datetime, timezone
import requests
from pathlib import Path
from sqlalchemy import select
from .celery_app import celery
from .db import save_result, SessionLocal
from .models import League, Fixture, SelectedFixture


@celery.task(name="tasks.add")
def add(x: int, y: int):
    res = x + y
    # 记录到外部 PostgreSQL
    save_result(celery_task_id=add.request.id, result=str(res))
    return res


@celery.task(name="tasks.import_leagues")
def import_leagues():
    from .settings import settings
    url = "https://v3.football.api-sports.io/leagues"
    headers = {"x-apisports-key": settings.API_FOOTBALL_KEY}
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    items = data.get("response") or []
    created = 0
    updated = 0
    with SessionLocal() as session:
        for item in items:
            league = item.get("league") or {}
            country = item.get("country") or {}
            league_id = league.get("id")
            if league_id is None:
                continue
            obj = session.execute(select(League).where(League.league_id == league_id)).scalar_one_or_none()
            values = {
                "name": league.get("name") or "",
                "type": league.get("type"),
                "logo_url": league.get("logo"),
                "country_name": country.get("name"),
                "country_code": country.get("code"),
                "country_flag_url": country.get("flag"),
            }
            if obj:
                for k, v in values.items():
                    setattr(obj, k, v)
                updated += 1
            else:
                obj = League(league_id=league_id, **values)
                session.add(obj)
                created += 1
        session.commit()
    req_id = getattr(import_leagues.request, "id", None) or "import-leagues-local"
    save_result(celery_task_id=req_id, result=json.dumps({"created": created, "updated": updated}))
    return {"created": created, "updated": updated}


@celery.task(name="tasks.fetch_fixtures_for_date")
def fetch_fixtures_for_date(day: str):
    from .settings import settings
    url = "https://v3.football.api-sports.io/fixtures"
    headers = {"x-apisports-key": settings.API_FOOTBALL_KEY}
    params = {"date": day, "timezone": "UTC"}
    resp = requests.get(url, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    created = 0
    updated = 0
    items = data.get("response") or []
    with SessionLocal() as session:
        for item in items:
            fixt = item.get("fixture") or {}
            league = item.get("league") or {}
            teams = item.get("teams") or {}
            goals = item.get("goals") or {}
            score = item.get("score") or {}

            fixture_id = fixt.get("id")
            if fixture_id is None:
                continue

            obj = session.execute(select(Fixture).where(Fixture.fixture_id == fixture_id)).scalar_one_or_none()
            dt = fixt.get("date")
            match_dt = None
            if dt:
                try:
                    match_dt = datetime.fromisoformat(dt).astimezone(timezone.utc)
                except Exception:
                    match_dt = None

            values = {
                "league_id": league.get("id"),
                "league_name": league.get("name"),
                "country_name": league.get("country"),
                "season": league.get("season"),
                "round": league.get("round"),
                "match_date": match_dt,
                "status_short": (fixt.get("status") or {}).get("short"),
                "status_long": (fixt.get("status") or {}).get("long"),
                "venue_id": (fixt.get("venue") or {}).get("id"),
                "venue_name": (fixt.get("venue") or {}).get("name"),
                "venue_city": (fixt.get("venue") or {}).get("city"),
                "home_team_id": (teams.get("home") or {}).get("id"),
                "home_team_name": (teams.get("home") or {}).get("name"),
                "away_team_id": (teams.get("away") or {}).get("id"),
                "away_team_name": (teams.get("away") or {}).get("name"),
                "goals_home": goals.get("home"),
                "goals_away": goals.get("away"),
                "halftime_home": ((score.get("halftime") or {}).get("home")),
                "halftime_away": ((score.get("halftime") or {}).get("away")),
                "fulltime_home": ((score.get("fulltime") or {}).get("home")),
                "fulltime_away": ((score.get("fulltime") or {}).get("away")),
            }
            if obj:
                for k, v in values.items():
                    setattr(obj, k, v)
                updated += 1
            else:
                obj = Fixture(fixture_id=fixture_id, **values)
                session.add(obj)
                created += 1
        session.commit()
    req_id = getattr(fetch_fixtures_for_date.request, "id", None) or f"fixtures-{day}"
    save_result(celery_task_id=req_id, result=json.dumps({"created": created, "updated": updated, "day": day}))
    return {"created": created, "updated": updated, "day": day}


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
