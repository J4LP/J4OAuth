"""empty message

Revision ID: 406cccb640c3
Revises: None
Create Date: 2014-02-03 15:40:56.201790

"""

# revision identifiers, used by Alembic.
revision = '406cccb640c3'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('client',
    sa.Column('name', sa.String(length=40), nullable=True),
    sa.Column('description', sa.String(length=400), nullable=True),
    sa.Column('user_id', sa.String(length=255), nullable=True),
    sa.Column('client_id', sa.String(length=40), nullable=False),
    sa.Column('client_secret', sa.String(length=55), nullable=False),
    sa.Column('is_confidential', sa.Boolean(), nullable=True),
    sa.Column('_redirect_uris', sa.Text(), nullable=True),
    sa.Column('_default_scopes', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('client_id')
    )
    op.create_index('ix_client_client_secret', 'client', ['client_secret'], unique=True)
    op.create_table('grant',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.String(length=255), nullable=True),
    sa.Column('client_id', sa.String(length=40), nullable=False),
    sa.Column('code', sa.String(length=255), nullable=False),
    sa.Column('redirect_uri', sa.String(length=255), nullable=True),
    sa.Column('expires', sa.DateTime(), nullable=True),
    sa.Column('_scopes', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['client_id'], ['client.client_id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_grant_code', 'grant', ['code'], unique=False)
    op.create_table('token',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('client_id', sa.String(length=40), nullable=False),
    sa.Column('user_id', sa.String(length=255), nullable=True),
    sa.Column('token_type', sa.String(length=40), nullable=True),
    sa.Column('access_token', sa.String(length=255), nullable=True),
    sa.Column('refresh_token', sa.String(length=255), nullable=True),
    sa.Column('expires', sa.DateTime(), nullable=True),
    sa.Column('_scopes', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['client_id'], ['client.client_id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('access_token'),
    sa.UniqueConstraint('refresh_token')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('token')
    op.drop_index('ix_grant_code', 'grant')
    op.drop_table('grant')
    op.drop_index('ix_client_client_secret', 'client')
    op.drop_table('client')
    ### end Alembic commands ###
