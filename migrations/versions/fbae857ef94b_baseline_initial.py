"""baseline_initial

Revision ID: fbae857ef94b
Revises:
Create Date: 2026-05-19 23:13:05.411001

基线迁移：全量6张表初始创建
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "fbae857ef94b"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "upload_files",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("filename", sa.String(255), nullable=False, index=True),
        sa.Column("file_path", sa.String(512), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.String(100), nullable=True, index=True),
        sa.Column("upload_time", sa.DateTime(), nullable=False),
        sa.Column("file_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="uploaded"),
    )

    op.create_table(
        "analysis_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.String(100), nullable=True, index=True),
        sa.Column("fan_model", sa.String(100), nullable=True, index=True),
        sa.Column("analysis_type", sa.String(100), nullable=False),
        sa.Column("input_files", sa.Text(), nullable=False),
        sa.Column("output_files", sa.Text(), nullable=False),
        sa.Column("best_speed", sa.String(100), nullable=True),
        sa.Column("analysis_time", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="completed"),
    )

    op.create_table(
        "chart_cache",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("cache_key", sa.String(255), nullable=False, unique=True, index=True),
        sa.Column("chart_data", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("last_accessed", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "system_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("log_time", sa.DateTime(), nullable=False),
        sa.Column("log_level", sa.String(20), nullable=False, index=True),
        sa.Column("module", sa.String(100), nullable=False, index=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("user_id", sa.String(100), nullable=True, index=True),
        sa.Column("ip_address", sa.String(50), nullable=True),
        sa.Column("error_trace", sa.Text(), nullable=True),
    )

    op.create_table(
        "outputs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("filename", sa.String(255), nullable=False, index=True),
        sa.Column("file_path", sa.String(512), nullable=False),
        sa.Column("file_type", sa.String(20), nullable=False, server_default="unknown"),
        sa.Column("file_size", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(50), nullable=False, server_default="completed"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("user_id", sa.String(100), nullable=True, index=True),
        sa.Column("fan_model", sa.String(100), nullable=True),
        sa.Column("analysis_type", sa.String(100), nullable=True),
        sa.Column("project_id", sa.Integer(), nullable=True),
    )

    op.create_table(
        "balancer_models",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("model_name", sa.String(100), nullable=False, unique=True, index=True),
        sa.Column("manufacturer", sa.String(100), nullable=True),
        sa.Column("max_speed", sa.String(50), nullable=True),
        sa.Column("max_radius", sa.String(50), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.sql.expression.true()
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )


def downgrade():
    op.drop_table("balancer_models")
    op.drop_table("outputs")
    op.drop_table("system_logs")
    op.drop_table("chart_cache")
    op.drop_table("analysis_results")
    op.drop_table("upload_files")
