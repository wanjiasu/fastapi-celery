from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "odds_quotes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("fixture_id", sa.Integer(), nullable=False),
        sa.Column("bookmaker_id", sa.Integer()),
        sa.Column("bookmaker_name", sa.String(length=255)),
        sa.Column("bet_id", sa.Integer()),
        sa.Column("bet_name", sa.String(length=255)),
        sa.Column("selection", sa.String(length=255)),
        sa.Column("odd", sa.String(length=20)),
        sa.Column("update_time", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_odds_quotes_fixture", "odds_quotes", ["fixture_id"]) 
    op.create_index("ix_odds_quotes_bookmaker_bet", "odds_quotes", ["bookmaker_id", "bet_id"]) 
    op.create_unique_constraint(
        "uq_odds_quotes_unique",
        "odds_quotes",
        ["fixture_id", "bookmaker_id", "bet_id", "selection", "update_time"],
    )


def downgrade():
    op.drop_constraint("uq_odds_quotes_unique", "odds_quotes", type_="unique")
    op.drop_index("ix_odds_quotes_bookmaker_bet", table_name="odds_quotes")
    op.drop_index("ix_odds_quotes_fixture", table_name="odds_quotes")
    op.drop_table("odds_quotes")
