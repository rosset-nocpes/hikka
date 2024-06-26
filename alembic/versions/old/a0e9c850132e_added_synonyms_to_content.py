"""Added synonyms to content

Revision ID: a0e9c850132e
Revises: e34c01aab281
Create Date: 2024-03-09 20:56:26.179850

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "a0e9c850132e"
down_revision = "e34c01aab281"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "service_content_characters",
        sa.Column(
            "synonyms",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="[]",
            nullable=False,
        ),
    )
    op.add_column(
        "service_content_companies",
        sa.Column(
            "synonyms",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="[]",
            nullable=False,
        ),
    )
    op.add_column(
        "service_content_people",
        sa.Column(
            "synonyms",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="[]",
            nullable=False,
        ),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("service_content_people", "synonyms")
    op.drop_column("service_content_companies", "synonyms")
    op.drop_column("service_content_characters", "synonyms")
    # ### end Alembic commands ###
