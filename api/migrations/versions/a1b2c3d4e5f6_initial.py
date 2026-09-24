# Alembic initial migration
"""Initial migration for ClipForge

Revision ID: a1b2c3d4e5f6
Revises: 
Create Date: 2026-09-24 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as pg
from datetime import datetime, timezone

revision = 'a1b2c3d4e5f6'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('users',
        sa.Column('id', pg.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('organization_id', pg.UUID(as_uuid=True), nullable=True),
        sa.Column('role', sa.String(50), nullable=False, server_default='creator'),
        sa.Column('credits_balance', sa.Float, nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )

    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_created_at'), 'users', ['created_at'])

    op.create_table('organizations',
        sa.Column('id', pg.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(255), nullable=False),
        sa.Column('plan', sa.String(50), nullable=False, server_default='free'),
        sa.Column('stripe_customer_id', sa.String(255), nullable=True),
        sa.Column('credits_total', sa.Float, nullable=False, server_default='0'),
        sa.Column('credits_used', sa.Float, nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )

    op.create_table('members',
        sa.Column('id', pg.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', pg.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', pg.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(50), nullable=False, server_default='member'),
        sa.Column('joined_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('projects',
        sa.Column('id', pg.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', pg.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('source_type', sa.String(50), nullable=True),
        sa.Column('source_url', sa.String(2048), nullable=True),
        sa.Column('source_path', sa.String(512), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index(op.f('ix_projects_user_id'), 'projects', ['user_id'])
    op.create_index(op.f('ix_projects_created_at'), 'projects', ['created_at'])
    op.create_index(op.f('ix_projects_status'), 'projects', ['status'])

    op.create_table('videos',
        sa.Column('id', pg.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', pg.UUID(as_uuid=True), nullable=False),
        sa.Column('original_filename', sa.String(512), nullable=False),
        sa.Column('storage_path', sa.String(1024), nullable=True),
        sa.Column('duration_seconds', sa.Float, nullable=True),
        sa.Column('resolution', sa.String(20), nullable=True),
        sa.Column('file_size_bytes', sa.Integer, nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='uploading'),
        sa.Column('thumbnail_url', sa.String(1024), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index(op.f('ix_videos_project_id'), 'videos', ['project_id'])
    op.create_index(op.f('ix_videos_status'), 'videos', ['status'])

    op.create_table('transcripts',
        sa.Column('id', pg.UUID(as_uuid=True), nullable=False),
        sa.Column('video_id', pg.UUID(as_uuid=True), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('language', sa.String(10), nullable=True),
        sa.Column('content', pg.JSON, nullable=True),
        sa.Column('full_text', sa.Text, nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index(op.f('ix_transcripts_video_id'), 'transcripts', ['video_id'])
    op.create_index(op.f('ix_transcripts_status'), 'transcripts', ['status'])

    op.create_table('clip_candidates',
        sa.Column('id', pg.UUID(as_uuid=True), nullable=False),
        sa.Column('video_id', pg.UUID(as_uuid=True), nullable=False),
        sa.Column('start_time', sa.Float, nullable=False),
        sa.Column('end_time', sa.Float, nullable=False),
        sa.Column('score', sa.Float, nullable=False),
        sa.Column('hook_text', sa.Text, nullable=True),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('confidence', sa.Float, nullable=True),
        sa.Column('strategy', sa.String(10), nullable=True),
        sa.Column('metadata', pg.JSON, nullable=True),
        sa.Column('selected', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index(op.f('ix_clip_candidates_video_score'), 'clip_candidates', ['video_id', 'score'], postgresql_ops={'score': 'DESC'})

    op.create_table('clips',
        sa.Column('id', pg.UUID(as_uuid=True), nullable=False),
        sa.Column('video_id', pg.UUID(as_uuid=True), nullable=False),
        sa.Column('candidate_id', pg.UUID(as_uuid=True), nullable=True),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('hashtags', pg.JSON, nullable=True),
        sa.Column('start_time', sa.Float, nullable=False),
        sa.Column('end_time', sa.Float, nullable=False),
        sa.Column('reframe_path', pg.JSON, nullable=True),
        sa.Column('aspect_ratio', sa.String(10), nullable=False, server_default='9:16'),
        sa.Column('caption_style_id', pg.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='draft'),
        sa.Column('output_url', sa.String(1024), nullable=True),
        sa.Column('thumbnail_url', sa.String(1024), nullable=True),
        sa.Column('credits_used', sa.Float, nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index(op.f('ix_clips_video_id'), 'clips', ['video_id'])
    op.create_index(op.f('ix_clips_status'), 'clips', ['status'])

    op.create_table('caption_styles',
        sa.Column('id', pg.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('font_family', sa.String(100), nullable=False, server_default='Inter'),
        sa.Column('font_size', sa.Integer, nullable=False, server_default='24'),
        sa.Column('font_color', sa.String(20), nullable=False, server_default='#FFFFFF'),
        sa.Column('background_color', sa.String(20), nullable=False, server_default='#000000'),
        sa.Column('background_opacity', sa.Float, nullable=False, server_default='0.7'),
        sa.Column('outline', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('outline_color', sa.String(20), nullable=False, server_default='#000000'),
        sa.Column('shadow', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('position', sa.String(20), nullable=False, server_default='bottom'),
        sa.Column('max_words_per_line', sa.Integer, nullable=False, server_default='5'),
        sa.Column('animation_type', sa.String(50), nullable=False, server_default='fade'),
        sa.Column('preset_data', pg.JSON, nullable=True),
        sa.Column('is_brand_default', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('organization_id', pg.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('render_jobs',
        sa.Column('id', pg.UUID(as_uuid=True), nullable=False),
        sa.Column('clip_id', pg.UUID(as_uuid=True), nullable=False),
        sa.Column('render_type', sa.String(50), nullable=False, server_default='preview'),
        sa.Column('resolution', sa.String(20), nullable=False, server_default='1080x1920'),
        sa.Column('status', sa.String(50), nullable=False, server_default='queued'),
        sa.Column('progress', sa.Float, nullable=False, server_default='0'),
        sa.Column('estimated_time_seconds', sa.Integer, nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('retry_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('attempts', sa.Integer, nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index(op.f('ix_render_jobs_clip_id'), 'render_jobs', ['clip_id'])
    op.create_index(op.f('ix_render_jobs_status'), 'render_jobs', ['status'])

    op.create_table('render_outputs',
        sa.Column('id', pg.UUID(as_uuid=True), nullable=False),
        sa.Column('render_job_id', pg.UUID(as_uuid=True), nullable=False),
        sa.Column('storage_path', sa.String(1024), nullable=False),
        sa.Column('file_size_bytes', sa.Integer, nullable=True),
        sa.Column('duration_seconds', sa.Float, nullable=True),
        sa.Column('resolution', sa.String(20), nullable=True),
        sa.Column('format', sa.String(20), nullable=False, server_default='mp4'),
        sa.Column('checksum', sa.String(64), nullable=True),
        sa.Column('signed_url', sa.String(1024), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index(op.f('ix_render_outputs_render_job_id'), 'render_outputs', ['render_job_id'])

    op.create_table('ai_jobs',
        sa.Column('id', pg.UUID(as_uuid=True), nullable=False),
        sa.Column('job_type', sa.String(50), nullable=False),
        sa.Column('model_used', sa.String(100), nullable=True),
        sa.Column('tokens_used', sa.Integer, nullable=False, server_default='0'),
        sa.Column('cost_credits', sa.Float, nullable=False, server_default='0'),
        sa.Column('provider', sa.String(50), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index(op.f('ix_ai_jobs_status'), 'ai_jobs', ['status'])

    op.create_table('usage_records',
        sa.Column('id', pg.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', pg.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', pg.UUID(as_uuid=True), nullable=True),
        sa.Column('job_type', sa.String(50), nullable=False),
        sa.Column('credits_consumed', sa.Float, nullable=False),
        sa.Column('metadata', pg.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index(op.f('ix_usage_user_created'), 'usage_records', ['user_id', 'created_at'])

    op.create_table('subscriptions',
        sa.Column('id', pg.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', pg.UUID(as_uuid=True), nullable=False),
        sa.Column('stripe_subscription_id', sa.String(255), nullable=True),
        sa.Column('plan', sa.String(50), nullable=False, server_default='free'),
        sa.Column('credits_total', sa.Float, nullable=False, server_default='0'),
        sa.Column('credits_used', sa.Float, nullable=False, server_default='0'),
        sa.Column('current_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index(op.f('ix_subscriptions_organization_id'), 'subscriptions', ['organization_id'])
    op.create_index(op.f('ix_subscriptions_status'), 'subscriptions', ['status'])

    op.create_table('api_keys',
        sa.Column('id', pg.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', pg.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', pg.UUID(as_uuid=True), nullable=True),
        sa.Column('key_hash', sa.String(255), nullable=False),
        sa.Column('name', sa.String(100), nullable=True),
        sa.Column('permissions', pg.JSON, nullable=True),
        sa.Column('rate_limit', sa.Integer, nullable=False, server_default='100'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index(op.f('ix_api_keys_user_id'), 'api_keys', ['user_id'])
    op.create_index(op.f('ix_api_keys_is_active'), 'api_keys', ['is_active'])

    op.create_table('scheduled_posts',
        sa.Column('id', pg.UUID(as_uuid=True), nullable=False),
        sa.Column('clip_id', pg.UUID(as_uuid=True), nullable=False),
        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('scheduled_for', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='scheduled'),
        sa.Column('content', pg.JSON, nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index(op.f('ix_scheduled_posts_status'), 'scheduled_posts', ['status'])
    op.create_index(op.f('ix_scheduled_posts_scheduled_for'), 'scheduled_posts', ['scheduled_for'])

    # Create foreign key constraints
    op.create_foreign_key('fk_projects_users', 'projects', 'users', ['user_id'], ['id'])
    op.create_foreign_key('fk_videos_projects', 'videos', 'projects', ['project_id'], ['id'])
    op.create_foreign_key('fk_transcripts_videos', 'transcripts', 'videos', ['video_id'], ['id'])
    op.create_foreign_key('fk_clip_candidates_videos', 'clip_candidates', 'videos', ['video_id'], ['id'])
    op.create_foreign_key('fk_clips_videos', 'clips', 'videos', ['video_id'], ['id'])
    op.create_foreign_key('fk_clips_candidates', 'clips', 'clip_candidates', ['candidate_id'], ['id'])
    op.create_foreign_key('fk_clips_caption_styles', 'clips', 'caption_styles', ['caption_style_id'], ['id'])
    op.create_foreign_key('fk_render_jobs_clips', 'render_jobs', 'clips', ['clip_id'], ['id'])
    op.create_foreign_key('fk_render_outputs_render_jobs', 'render_outputs', 'render_jobs', ['render_job_id'], ['id'])
    op.create_foreign_key('fk_usage_users', 'usage_records', 'users', ['user_id'], ['id'])
    op.create_foreign_key('fk_usage_organizations', 'usage_records', 'organizations', ['organization_id'], ['id'])
    op.create_foreign_key('fk_subscriptions_organizations', 'subscriptions', 'organizations', ['organization_id'], ['id'])
    op.create_foreign_key('fk_api_keys_users', 'api_keys', 'users', ['user_id'], ['id'])
    op.create_foreign_key('fk_api_keys_organizations', 'api_keys', 'organizations', ['organization_id'], ['id'])
    op.create_foreign_key('fk_scheduled_posts_clips', 'scheduled_posts', 'clips', ['clip_id'], ['id'])
    op.create_foreign_key('fk_members_organizations', 'members', 'organizations', ['organization_id'], ['id'])
    op.create_foreign_key('fk_members_users', 'members', 'users', ['user_id'], ['id'])


def downgrade():
    op.drop_constraint('fk_scheduled_posts_clips', 'scheduled_posts', type_='foreignkey')
    op.drop_constraint('fk_api_keys_users', 'api_keys', type_='foreignkey')
    op.drop_constraint('fk_api_keys_organizations', 'api_keys', type_='foreignkey')
    op.drop_constraint('fk_subscriptions_organizations', 'subscriptions', type_='foreignkey')
    op.drop_constraint('fk_usage_organizations', 'usage_records', type_='foreignkey')
    op.drop_constraint('fk_usage_users', 'usage_records', type_='foreignkey')
    op.drop_constraint('fk_render_outputs_render_jobs', 'render_outputs', type_='foreignkey')
    op.drop_constraint('fk_render_jobs_clips', 'render_jobs', type_='foreignkey')
    op.drop_constraint('fk_clips_caption_styles', 'clips', type_='foreignkey')
    op.drop_constraint('fk_clips_candidates', 'clips', type_='foreignkey')
    op.drop_constraint('fk_clips_videos', 'clips', type_='foreignkey')
    op.drop_constraint('fk_clip_candidates_videos', 'clip_candidates', type_='foreignkey')
    op.drop_constraint('fk_transcripts_videos', 'transcripts', type_='foreignkey')
    op.drop_constraint('fk_videos_projects', 'videos', type_='foreignkey')
    op.drop_constraint('fk_projects_users', 'projects', type_='foreignkey')
    op.drop_constraint('fk_members_users', 'members', type_='foreignkey')
    op.drop_constraint('fk_members_organizations', 'members', type_='foreignkey')

    op.drop_index('ix_scheduled_posts_scheduled_for', table_name='scheduled_posts')
    op.drop_index('ix_scheduled_posts_status', table_name='scheduled_posts')
    op.drop_index('ix_api_keys_is_active', table_name='api_keys')
    op.drop_index('ix_api_keys_user_id', table_name='api_keys')
    op.drop_index('ix_subscriptions_status', table_name='subscriptions')
    op.drop_index('ix_subscriptions_organization_id', table_name='subscriptions')
    op.drop_index('ix_usage_user_created', table_name='usage_records')
    op.drop_index('ix_render_outputs_render_job_id', table_name='render_outputs')
    op.drop_index('ix_render_jobs_status', table_name='render_jobs')
    op.drop_index('ix_render_jobs_clip_id', table_name='render_jobs')
    op.drop_index('ix_render_job_id', table_name='render_jobs')
    op.drop_index('ix_ai_jobs_status', table_name='ai_jobs')
    op.drop_index('ix_transcripts_status', table_name='transcripts')
    op.drop_index('ix_transcripts_video_id', table_name='transcripts')
    op.drop_index('ix_videos_status', table_name='videos')
    op.drop_index('ix_videos_project_id', table_name='videos')
    op.drop_index('ix_projects_status', table_name='projects')
    op.drop_index('ix_projects_created_at', table_name='projects')
    op.drop_index('ix_projects_user_id', table_name='projects')
    op.drop_index('ix_users_created_at', table_name='users')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_index('ix_clip_candidates_video_score', table_name='clip_candidates')

    op.drop_table('scheduled_posts')
    op.drop_table('api_keys')
    op.drop_table('subscriptions')
    op.drop_table('usage_records')
    op.drop_table('ai_jobs')
    op.drop_table('render_outputs')
    op.drop_table('render_jobs')
    op.drop_table('caption_styles')
    op.drop_table('clips')
    op.drop_table('clip_candidates')
    op.drop_table('transcripts')
    op.drop_table('videos')
    op.drop_table('projects')
    op.drop_table('members')
    op.drop_table('organizations')
    op.drop_table('users')
