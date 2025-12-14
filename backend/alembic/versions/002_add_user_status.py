"""Add user status column

Revision ID: 002_add_user_status
Revises: 001_add_winners_tables
Create Date: 2024-01-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_add_user_status'
down_revision = '001_add_winners_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Créer l'enum UserStatus si nécessaire
    conn = op.get_bind()
    result = conn.execute(sa.text("SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'userstatus')"))
    enum_exists = result.scalar()
    
    if not enum_exists:
        op.execute("CREATE TYPE userstatus AS ENUM ('pending', 'approved', 'rejected')")
    
    # Ajouter la colonne status à la table users
    op.add_column('users', sa.Column('status', postgresql.ENUM('pending', 'approved', 'rejected', name='userstatus', create_type=False), server_default='pending', nullable=True))
    
    # Mettre à jour les utilisateurs existants pour qu'ils soient approuvés par défaut
    op.execute("UPDATE users SET status = 'approved' WHERE status IS NULL")


def downgrade() -> None:
    op.drop_column('users', 'status')
    op.execute("DROP TYPE IF EXISTS userstatus")





Revision ID: 002_add_user_status
Revises: 001_add_winners_tables
Create Date: 2024-01-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_add_user_status'
down_revision = '001_add_winners_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Créer l'enum UserStatus si nécessaire
    conn = op.get_bind()
    result = conn.execute(sa.text("SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'userstatus')"))
    enum_exists = result.scalar()
    
    if not enum_exists:
        op.execute("CREATE TYPE userstatus AS ENUM ('pending', 'approved', 'rejected')")
    
    # Ajouter la colonne status à la table users
    op.add_column('users', sa.Column('status', postgresql.ENUM('pending', 'approved', 'rejected', name='userstatus', create_type=False), server_default='pending', nullable=True))
    
    # Mettre à jour les utilisateurs existants pour qu'ils soient approuvés par défaut
    op.execute("UPDATE users SET status = 'approved' WHERE status IS NULL")


def downgrade() -> None:
    op.drop_column('users', 'status')
    op.execute("DROP TYPE IF EXISTS userstatus")



