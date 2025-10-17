"""add preference tables

Revision ID: 003
Revises: 002
Create Date: 2025-10-14 12:30:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # User Topic Preferences
    op.create_table(
        'user_topic_preferences',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('topic_category', sa.String(50), nullable=False),
        sa.Column('subcategory', sa.String(100), nullable=False),
        sa.Column('preference_weight', sa.DECIMAL(4, 3), nullable=False, server_default='0.500'),
        sa.Column('confidence_score', sa.DECIMAL(3, 2), nullable=False, server_default='0.50'),
        sa.Column('interaction_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_interaction', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'topic_category', 'subcategory')
    )
    op.create_index('idx_user_topic_weight', 'user_topic_preferences', ['user_id', 'preference_weight'])
    op.create_index('idx_topic_category', 'user_topic_preferences', ['topic_category', 'subcategory'])
    
    # User Depth Preferences
    op.create_table(
        'user_depth_preferences',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('surface_weight', sa.DECIMAL(4, 3), nullable=False, server_default='0.167'),
        sa.Column('light_weight', sa.DECIMAL(4, 3), nullable=False, server_default='0.167'),
        sa.Column('moderate_weight', sa.DECIMAL(4, 3), nullable=False, server_default='0.167'),
        sa.Column('detailed_weight', sa.DECIMAL(4, 3), nullable=False, server_default='0.167'),
        sa.Column('deep_weight', sa.DECIMAL(4, 3), nullable=False, server_default='0.167'),
        sa.Column('academic_weight', sa.DECIMAL(4, 3), nullable=False, server_default='0.165'),
        sa.Column('preferred_depth', sa.Integer(), nullable=False, server_default='2'),
        sa.Column('alpha_prior', sa.DECIMAL(5, 2), nullable=False, server_default='1.0'),
        sa.Column('beta_prior', sa.DECIMAL(5, 2), nullable=False, server_default='1.0'),
        sa.Column('confidence_score', sa.DECIMAL(3, 2), nullable=False, server_default='0.50'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    
    # User Surprise Preferences
    op.create_table(
        'user_surprise_preferences',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('predictable_weight', sa.DECIMAL(4, 3), nullable=False, server_default='0.167'),
        sa.Column('familiar_weight', sa.DECIMAL(4, 3), nullable=False, server_default='0.167'),
        sa.Column('balanced_weight', sa.DECIMAL(4, 3), nullable=False, server_default='0.167'),
        sa.Column('adventurous_weight', sa.DECIMAL(4, 3), nullable=False, server_default='0.167'),
        sa.Column('exploratory_weight', sa.DECIMAL(4, 3), nullable=False, server_default='0.167'),
        sa.Column('radical_weight', sa.DECIMAL(4, 3), nullable=False, server_default='0.165'),
        sa.Column('surprise_tolerance', sa.Integer(), nullable=False, server_default='2'),
        sa.Column('exploration_rate', sa.DECIMAL(3, 2), nullable=False, server_default='0.40'),
        sa.Column('learning_rate', sa.DECIMAL(4, 3), nullable=False, server_default='0.010'),
        sa.Column('q_values', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('confidence_score', sa.DECIMAL(3, 2), nullable=False, server_default='0.50'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    
    # User Contextual Preferences
    op.create_table(
        'user_contextual_preferences',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('context_type', sa.String(50), nullable=False),
        sa.Column('context_value', sa.String(100), nullable=False),
        sa.Column('topic_adjustments', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('depth_adjustment', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('surprise_adjustment', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('arm_pulls', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_reward', sa.DECIMAL(10, 4), nullable=False, server_default='0.0'),
        sa.Column('ucb_score', sa.DECIMAL(10, 4), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_user_context', 'user_contextual_preferences', ['user_id', 'context_type', 'context_value'], unique=True)
    
    # User Learning States
    op.create_table(
        'user_learning_states',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('hmm_states', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('lstm_model_state', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('bandit_arms_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('learning_confidence', sa.DECIMAL(3, 2), nullable=False, server_default='0.50'),
        sa.Column('hmm_accuracy', sa.DECIMAL(3, 2), nullable=True),
        sa.Column('lstm_accuracy', sa.DECIMAL(3, 2), nullable=True),
        sa.Column('bandit_regret', sa.DECIMAL(10, 4), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id')
    )
    
    # User Behavioral Signals
    op.create_table(
        'user_behavioral_signals',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('podcast_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('signal_type', sa.String(50), nullable=False),
        sa.Column('signal_category', sa.String(50), nullable=False),
        sa.Column('signal_value', sa.DECIMAL(5, 3), nullable=False),
        sa.Column('signal_weight', sa.DECIMAL(3, 2), nullable=False),
        sa.Column('context_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('raw_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('processed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_user_behavioral_signals', 'user_behavioral_signals', ['user_id'])
    op.create_index('idx_user_signal_type', 'user_behavioral_signals', ['user_id', 'signal_type', 'created_at'])
    op.create_index('idx_signal_processing', 'user_behavioral_signals', ['processed', 'created_at'])
    
    # User Cold Start Data
    op.create_table(
        'user_cold_start_data',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('questionnaire_responses', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('age_range', sa.String(20), nullable=True),
        sa.Column('education_level', sa.String(50), nullable=True),
        sa.Column('occupation', sa.String(100), nullable=True),
        sa.Column('location', sa.String(100), nullable=True),
        sa.Column('cluster_id', sa.Integer(), nullable=True),
        sa.Column('cluster_confidence', sa.DECIMAL(3, 2), nullable=True),
        sa.Column('exploration_rate', sa.DECIMAL(3, 2), nullable=False, server_default='0.40'),
        sa.Column('questions_answered', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('onboarding_complete', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )


def downgrade() -> None:
    op.drop_table('user_cold_start_data')
    op.drop_table('user_behavioral_signals')
    op.drop_table('user_learning_states')
    op.drop_table('user_contextual_preferences')
    op.drop_table('user_surprise_preferences')
    op.drop_table('user_depth_preferences')
    op.drop_table('user_topic_preferences')
