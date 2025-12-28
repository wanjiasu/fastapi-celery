from alembic import op
import sqlalchemy as sa

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "ai_eval",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("fixture_id", sa.Integer(), nullable=False),
        sa.Column("strategy", sa.String(length=50)),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_ai_eval_fixture", "ai_eval", ["fixture_id"])
    op.create_unique_constraint("uq_ai_eval_fixture_strategy", "ai_eval", ["fixture_id", "strategy"])


def downgrade():
    op.drop_constraint("uq_ai_eval_fixture_strategy", "ai_eval", type_="unique")
    op.drop_index("ix_ai_eval_fixture", table_name="ai_eval")
    op.drop_table("ai_eval")
