import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv


def main():
    load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")
    api_key = os.getenv("API_FOOTBALL_KEY")
    if not api_key:
        print("API_FOOTBALL_KEY is missing", file=sys.stderr)
        sys.exit(1)

    if len(sys.argv) < 1 + 1:
        print("usage: python get_odds.py <fixture_id>", file=sys.stderr)
        sys.exit(2)

    fixture_id = sys.argv[1]
    url = "https://v3.football.api-sports.io/odds"
    headers = {"x-apisports-key": api_key}
    params = {"fixture": fixture_id, "timezone": "UTC"}
    resp = requests.get(url, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    out_dir = Path(__file__).parent / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"odds_{fixture_id}.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(str(out_path))


if __name__ == "__main__":
    main()
