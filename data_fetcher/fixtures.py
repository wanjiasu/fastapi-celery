import requests
from datetime import datetime, timezone
from sqlalchemy import select
from app.settings import settings
from app.db import SessionLocal
from app.models import Fixture


def fetch_fixtures_for_date_data(day: str):
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
    return {"created": created, "updated": updated}
