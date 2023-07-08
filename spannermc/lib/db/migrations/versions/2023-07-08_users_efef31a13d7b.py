# type: ignore

"""users

Revision ID: efef31a13d7b
Revises: 
Create Date: 2023-07-08 13:51:02.886983

"""
import sqlalchemy as sa
from alembic import op
from litestar.contrib.sqlalchemy.types import GUID, ORA_JSONB, DateTimeUTC


__all__ = ["downgrade", "upgrade"]

sa.GUID = GUID
sa.DateTimeUTC = DateTimeUTC
sa.ORA_JSONB = ORA_JSONB

# revision identifiers, used by Alembic.
revision = 'efef31a13d7b'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
