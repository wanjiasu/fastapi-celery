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

    url = "https://v3.football.api-sports.io/odds/bets"
    headers = {"x-apisports-key": api_key}
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    out_dir = Path(__file__).parent / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "odds_bets.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(str(out_path))


if __name__ == "__main__":
    main()
