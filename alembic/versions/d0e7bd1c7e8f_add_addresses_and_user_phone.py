"""add_addresses_and_user_phone

Revision ID: d0e7bd1c7e8f
Revises: af8c15a6df53
Create Date: 2026-03-10 13:06:03.456848

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d0e7bd1c7e8f"
down_revision: str | Sequence[str] | None = "af8c15a6df53"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add phone_number to users table
    op.add_column("users", sa.Column("phone_number", sa.String(20), nullable=True))

    # Create addresses table
    op.create_table(
        "addresses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("street_address", sa.String(500), nullable=False),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("state", sa.String(100), nullable=False),
        sa.Column("zip_code", sa.String(20), nullable=False),
        sa.Column("country", sa.String(100), nullable=False),
        sa.Column("phone_number", sa.String(20), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_addresses_user_id", "addresses", ["user_id"])
    op.create_index("ix_addresses_is_default", "addresses", ["is_default"])

    # Add shipping_address_id to orders table
    op.add_column(
        "orders", sa.Column("shipping_address_id", sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        "fk_orders_shipping_address",
        "orders",
        "addresses",
        ["shipping_address_id"],
        ["id"],
    )
    op.create_index("ix_orders_shipping_address_id", "orders", ["shipping_address_id"])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop orders foreign key and column
    op.drop_index("ix_orders_shipping_address_id", table_name="orders")
    op.drop_constraint("fk_orders_shipping_address", "orders", type_="foreignkey")
    op.drop_column("orders", "shipping_address_id")

    # Drop addresses table
    op.drop_index("ix_addresses_is_default", table_name="addresses")
    op.drop_index("ix_addresses_user_id", table_name="addresses")
    op.drop_table("addresses")

    # Drop phone_number from users
    op.drop_column("users", "phone_number")
