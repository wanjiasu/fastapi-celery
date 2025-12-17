import json
import requests
from pathlib import Path
from sqlalchemy import select
from .celery_app import celery
from .db import save_result, SessionLocal
from .models import League


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
