from alembic import op
import sqlalchemy as sa

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "selected_fixtures",
        sa.Column("ai_eval_translations", sa.JSON(), nullable=True),
    )


def downgrade():
    op.drop_column("selected_fixtures", "ai_eval_translations")
