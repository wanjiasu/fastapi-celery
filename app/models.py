from datetime import datetime
from sqlalchemy import Integer, String, Text, DateTime, Numeric, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class League(Base):
    __tablename__ = "leagues"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    league_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str | None] = mapped_column(String(50))
    logo_url: Mapped[str | None] = mapped_column(Text)
    country_name: Mapped[str | None] = mapped_column(String(100))
    country_code: Mapped[str | None] = mapped_column(String(10))
    country_flag_url: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Fixture(Base):
    __tablename__ = "fixtures"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fixture_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)

    # league info
    league_id: Mapped[int | None] = mapped_column(Integer)
    league_name: Mapped[str | None] = mapped_column(String(255))
    country_name: Mapped[str | None] = mapped_column(String(100))
    season: Mapped[int | None] = mapped_column(Integer)
    round: Mapped[str | None] = mapped_column(String(50))

    # timing & status
    match_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status_short: Mapped[str | None] = mapped_column(String(10))
    status_long: Mapped[str | None] = mapped_column(String(100))

    # venue
    venue_id: Mapped[int | None] = mapped_column(Integer)
    venue_name: Mapped[str | None] = mapped_column(String(255))
    venue_city: Mapped[str | None] = mapped_column(String(100))

    # teams
    home_team_id: Mapped[int | None] = mapped_column(Integer)
    home_team_name: Mapped[str | None] = mapped_column(String(255))
    away_team_id: Mapped[int | None] = mapped_column(Integer)
    away_team_name: Mapped[str | None] = mapped_column(String(255))

    # goals
    goals_home: Mapped[int | None] = mapped_column(Integer)
    goals_away: Mapped[int | None] = mapped_column(Integer)

    halftime_home: Mapped[int | None] = mapped_column(Integer)
    halftime_away: Mapped[int | None] = mapped_column(Integer)
    fulltime_home: Mapped[int | None] = mapped_column(Integer)
    fulltime_away: Mapped[int | None] = mapped_column(Integer)

    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class SelectedFixture(Base):
    __tablename__ = "selected_fixtures"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fixture_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)

    league_id: Mapped[int | None] = mapped_column(Integer)
    league_name: Mapped[str | None] = mapped_column(String(255))
    country_name: Mapped[str | None] = mapped_column(String(100))
    season: Mapped[int | None] = mapped_column(Integer)
    round: Mapped[str | None] = mapped_column(String(50))

    match_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status_short: Mapped[str | None] = mapped_column(String(10))
    status_long: Mapped[str | None] = mapped_column(String(100))

    venue_id: Mapped[int | None] = mapped_column(Integer)
    venue_name: Mapped[str | None] = mapped_column(String(255))
    venue_city: Mapped[str | None] = mapped_column(String(100))

    home_team_id: Mapped[int | None] = mapped_column(Integer)
    home_team_name: Mapped[str | None] = mapped_column(String(255))
    away_team_id: Mapped[int | None] = mapped_column(Integer)
    away_team_name: Mapped[str | None] = mapped_column(String(255))

    goals_home: Mapped[int | None] = mapped_column(Integer)
    goals_away: Mapped[int | None] = mapped_column(Integer)

    halftime_home: Mapped[int | None] = mapped_column(Integer)
    halftime_away: Mapped[int | None] = mapped_column(Integer)
    fulltime_home: Mapped[int | None] = mapped_column(Integer)
    fulltime_away: Mapped[int | None] = mapped_column(Integer)

    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    ai_eval_translations: Mapped[dict | None] = mapped_column(JSON)


class OddsQuote(Base):
    __tablename__ = "odds_quotes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fixture_id: Mapped[int] = mapped_column(Integer, nullable=False)
    bookmaker_id: Mapped[int | None] = mapped_column(Integer)
    bookmaker_name: Mapped[str | None] = mapped_column(String(255))
    bet_id: Mapped[int | None] = mapped_column(Integer)
    bet_name: Mapped[str | None] = mapped_column(String(255))
    selection: Mapped[str | None] = mapped_column(String(255))
    odd: Mapped[str | None] = mapped_column(String(20))
    update_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
