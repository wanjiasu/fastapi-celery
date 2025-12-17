import requests
from datetime import datetime, timezone
from sqlalchemy import select
from app.settings import settings
from app.db import SessionLocal
from app.models import OddsQuote


def fetch_odds_for_fixture_data(fixture_id: int, bet_ids: set[int]):
    url = "https://v3.football.api-sports.io/odds"
    headers = {"x-apisports-key": settings.API_FOOTBALL_KEY}
    params = {"fixture": str(fixture_id), "timezone": "UTC"}
    resp = requests.get(url, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    inserted = 0
    items = data.get("response") or []
    update_str = None
    if items:
        update_str = items[0].get("update")
    update_dt = None
    if update_str:
        try:
            update_dt = datetime.fromisoformat(update_str).astimezone(timezone.utc)
        except Exception:
            update_dt = None
    with SessionLocal() as session:
        for it in items:
            bms = it.get("bookmakers") or []
            for bm in bms:
                bm_id = bm.get("id")
                bm_name = bm.get("name")
                bets = bm.get("bets") or []
                for bet in bets:
                    bid = bet.get("id")
                    if bid not in bet_ids:
                        continue
                    bname = bet.get("name")
                    vals = bet.get("values") or []
                    for v in vals:
                        sel = v.get("value")
                        odd = v.get("odd")
                        exists = session.execute(
                            select(OddsQuote).where(
                                OddsQuote.fixture_id == fixture_id,
                                OddsQuote.bookmaker_id == bm_id,
                                OddsQuote.bet_id == bid,
                                OddsQuote.selection == sel,
                                OddsQuote.update_time == update_dt,
                            )
                        ).scalar_one_or_none()
                        if exists:
                            continue
                        obj = OddsQuote(
                            fixture_id=fixture_id,
                            bookmaker_id=bm_id,
                            bookmaker_name=bm_name,
                            bet_id=bid,
                            bet_name=bname,
                            selection=sel,
                            odd=odd,
                            update_time=update_dt,
                        )
                        session.add(obj)
                        inserted += 1
        session.commit()
    return {"inserted": inserted}
