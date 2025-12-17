from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "selected_leagues",
        sa.Column("league_id", sa.Integer(), primary_key=True),
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION sync_selected_fixtures()
        RETURNS trigger AS $$
        BEGIN
          IF EXISTS (SELECT 1 FROM selected_leagues WHERE league_id = NEW.league_id) THEN
            INSERT INTO selected_fixtures (
              fixture_id, league_id, league_name, country_name, season, round,
              match_date, status_short, status_long, venue_id, venue_name, venue_city,
              home_team_id, home_team_name, away_team_id, away_team_name,
              goals_home, goals_away, halftime_home, halftime_away, fulltime_home, fulltime_away, updated_at
            )
            VALUES (
              NEW.fixture_id, NEW.league_id, NEW.league_name, NEW.country_name, NEW.season, NEW.round,
              NEW.match_date, NEW.status_short, NEW.status_long, NEW.venue_id, NEW.venue_name, NEW.venue_city,
              NEW.home_team_id, NEW.home_team_name, NEW.away_team_id, NEW.away_team_name,
              NEW.goals_home, NEW.goals_away, NEW.halftime_home, NEW.halftime_away, NEW.fulltime_home, NEW.fulltime_away, now()
            )
            ON CONFLICT (fixture_id) DO UPDATE SET
              league_id = EXCLUDED.league_id,
              league_name = EXCLUDED.league_name,
              country_name = EXCLUDED.country_name,
              season = EXCLUDED.season,
              round = EXCLUDED.round,
              match_date = EXCLUDED.match_date,
              status_short = EXCLUDED.status_short,
              status_long = EXCLUDED.status_long,
              venue_id = EXCLUDED.venue_id,
              venue_name = EXCLUDED.venue_name,
              venue_city = EXCLUDED.venue_city,
              home_team_id = EXCLUDED.home_team_id,
              home_team_name = EXCLUDED.home_team_name,
              away_team_id = EXCLUDED.away_team_id,
              away_team_name = EXCLUDED.away_team_name,
              goals_home = EXCLUDED.goals_home,
              goals_away = EXCLUDED.goals_away,
              halftime_home = EXCLUDED.halftime_home,
              halftime_away = EXCLUDED.halftime_away,
              fulltime_home = EXCLUDED.fulltime_home,
              fulltime_away = EXCLUDED.fulltime_away,
              updated_at = now();
          ELSE
            DELETE FROM selected_fixtures WHERE fixture_id = NEW.fixture_id;
          END IF;
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER fixtures_sync_selected
        AFTER INSERT OR UPDATE ON fixtures
        FOR EACH ROW EXECUTE FUNCTION sync_selected_fixtures();
        """
    )


def downgrade():
    op.execute("DROP TRIGGER IF EXISTS fixtures_sync_selected ON fixtures")
    op.execute("DROP FUNCTION IF EXISTS sync_selected_fixtures()")
    op.drop_table("selected_leagues")
