"""empty message

Revision ID: 4b01613bfbed
Revises: 406cccb640c3
Create Date: 2014-02-07 00:29:22.150808

"""

# revision identifiers, used by Alembic.
revision = '4b01613bfbed'
down_revision = '406cccb640c3'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('client', sa.Column('homepage', sa.String(length=255), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('client', 'homepage')
    ### end Alembic commands ###