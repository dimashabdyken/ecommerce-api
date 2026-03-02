"""add orders tables

Revision ID: af8c15a6df53
Revises: 3b7c0c2d58f1
Create Date: 2026-03-02 15:06:05.497043

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'af8c15a6df53'
down_revision: str | Sequence[str] | None = '3b7c0c2d58f1'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create orders table
    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("total_amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("stripe_payment_intent_id", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_orders_status"), "orders", ["status"], unique=False)
    op.create_index(op.f("ix_orders_stripe_payment_intent_id"), "orders", ["stripe_payment_intent_id"], unique=True)
    op.create_index(op.f("ix_orders_user_id"), "orders", ["user_id"], unique=False)

    # Create order_items table
    op.create_table(
        "order_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("price_at_purchase", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_order_items_order_id"), "order_items", ["order_id"], unique=False)
    op.create_index(op.f("ix_order_items_product_id"), "order_items", ["product_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_order_items_product_id"), table_name="order_items")
    op.drop_index(op.f("ix_order_items_order_id"), table_name="order_items")
    op.drop_table("order_items")
    op.drop_index(op.f("ix_orders_stripe_payment_intent_id"), table_name="orders")
    op.drop_index(op.f("ix_orders_status"), table_name="orders")
    op.drop_index(op.f("ix_orders_user_id"), table_name="orders")
    op.drop_table("orders")
