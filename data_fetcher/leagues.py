import requests
from sqlalchemy import select
from app.settings import settings
from app.db import SessionLocal
from app.models import League


def import_leagues_data():
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
                changed = 0
                for k, v in values.items():
                    if getattr(obj, k) != v:
                        setattr(obj, k, v)
                        changed += 1
                if changed:
                    updated += 1
            else:
                obj = League(league_id=league_id, **values)
                session.add(obj)
                created += 1
        session.commit()
    return {"created": created, "updated": updated}
