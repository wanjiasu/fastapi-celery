from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "selected_fixtures",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("fixture_id", sa.Integer(), nullable=False, unique=True),
        sa.Column("league_id", sa.Integer()),
        sa.Column("league_name", sa.String(length=255)),
        sa.Column("country_name", sa.String(length=100)),
        sa.Column("season", sa.Integer()),
        sa.Column("round", sa.String(length=50)),
        sa.Column("match_date", sa.DateTime(timezone=True)),
        sa.Column("status_short", sa.String(length=10)),
        sa.Column("status_long", sa.String(length=100)),
        sa.Column("venue_id", sa.Integer()),
        sa.Column("venue_name", sa.String(length=255)),
        sa.Column("venue_city", sa.String(length=100)),
        sa.Column("home_team_id", sa.Integer()),
        sa.Column("home_team_name", sa.String(length=255)),
        sa.Column("away_team_id", sa.Integer()),
        sa.Column("away_team_name", sa.String(length=255)),
        sa.Column("goals_home", sa.Integer()),
        sa.Column("goals_away", sa.Integer()),
        sa.Column("halftime_home", sa.Integer()),
        sa.Column("halftime_away", sa.Integer()),
        sa.Column("fulltime_home", sa.Integer()),
        sa.Column("fulltime_away", sa.Integer()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_selected_fixtures_date", "selected_fixtures", ["match_date"]) 
    op.create_index("ix_selected_fixtures_league", "selected_fixtures", ["league_id"]) 


def downgrade():
    op.drop_index("ix_selected_fixtures_league", table_name="selected_fixtures")
    op.drop_index("ix_selected_fixtures_date", table_name="selected_fixtures")
    op.drop_table("selected_fixtures")
