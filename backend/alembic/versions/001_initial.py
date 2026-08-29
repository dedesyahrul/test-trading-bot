"""Initial schema creation

Revision ID: 001_initial
Revises: 
Create Date: 2026-08-29 19:10:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    
    # users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('username', sa.String(50), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('is_admin', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('settings', postgresql.JSON(astext_type=sa.Text()), server_default='{}', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email'),
    )
    op.create_index('idx_users_username', 'users', ['username'])
    op.create_index('idx_users_email', 'users', ['email'])

    # chains table
    op.create_table(
        'chains',
        sa.Column('id', sa.String(20), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('native_token', sa.String(10), nullable=False),
        sa.Column('rpc_url', sa.String(255), nullable=False),
        sa.Column('explorer_url', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    # tokens table
    op.create_table(
        'tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('chain_id', sa.String(20), nullable=False),
        sa.Column('address', sa.String(255), nullable=False),
        sa.Column('symbol', sa.String(20), nullable=False),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('decimals', sa.Integer(), server_default='18', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['chain_id'], ['chains.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('chain_id', 'address', name='uq_token_chain_address'),
    )

    # wallets table
    op.create_table(
        'wallets',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chain_id', sa.String(20), nullable=False),
        sa.Column('address', sa.String(255), nullable=False),
        sa.Column('label', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('max_trade_amount', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('daily_loss_limit', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['chain_id'], ['chains.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'chain_id', name='uq_wallet_user_chain'),
    )

    # pairs table
    op.create_table(
        'pairs',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('chain_id', sa.String(20), nullable=False),
        sa.Column('base_token_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('quote_token_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('dex_name', sa.String(50), nullable=False),
        sa.Column('pair_address', sa.String(255), nullable=True),
        sa.Column('liquidity_usd', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('price_usd', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('is_watched', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['base_token_id'], ['tokens.id'], ),
        sa.ForeignKeyConstraint(['chain_id'], ['chains.id'], ),
        sa.ForeignKeyConstraint(['quote_token_id'], ['tokens.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('chain_id', 'base_token_id', 'quote_token_id', 'dex_name', name='uq_pair_unique'),
    )

    # market_snapshots table
    op.create_table(
        'market_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('pair_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('price_usd', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('price_change_1m', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('price_change_5m', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('price_change_1h', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('price_change_24h', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('volume_1m_usd', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('volume_5m_usd', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('volume_1h_usd', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('volume_24h_usd', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('liquidity_usd', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('buy_volume_24h', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('sell_volume_24h', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('buy_count_24h', sa.Integer(), nullable=True),
        sa.Column('sell_count_24h', sa.Integer(), nullable=True),
        sa.Column('market_cap_usd', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('fdv_usd', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['pair_id'], ['pairs.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('pair_id', 'timestamp', name='uq_snapshot_pair_timestamp'),
    )
    op.create_index('idx_market_snapshots_pair_id', 'market_snapshots', ['pair_id'])
    op.create_index('idx_market_snapshots_timestamp', 'market_snapshots', ['timestamp'])

    # risk_assessments table
    op.create_table(
        'risk_assessments',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('pair_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('risk_score', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('risk_level', sa.String(20), nullable=False),
        sa.Column('liquidity_risk', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('holder_risk', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('contract_risk', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('developer_risk', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('manipulation_risk', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('rug_pull_risk', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('slippage_risk', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('execution_risk', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('reasons', postgresql.JSON(astext_type=sa.Text()), server_default='[]', nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['pair_id'], ['pairs.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_risk_assessments_pair_id', 'risk_assessments', ['pair_id'])
    op.create_index('idx_risk_assessments_timestamp', 'risk_assessments', ['timestamp'])

    # features table
    op.create_table(
        'features',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('pair_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('return_1m', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('return_5m', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('return_1h', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('volatility_1h', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('momentum_1h', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('volume_growth_1h', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('volume_acceleration', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('volume_spike', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('buy_sell_ratio_1h', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('buy_pressure', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('liquidity_change', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('liquidity_ratio', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('raw_data', postgresql.JSON(astext_type=sa.Text()), server_default='{}', nullable=True),
        sa.ForeignKeyConstraint(['pair_id'], ['pairs.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('pair_id', 'timestamp', name='uq_feature_pair_timestamp'),
    )
    op.create_index('idx_features_pair_id', 'features', ['pair_id'])
    op.create_index('idx_features_timestamp', 'features', ['timestamp'])

    # predictions table
    op.create_table(
        'predictions',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('pair_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('model_id', sa.String(50), nullable=False),
        sa.Column('model_version', sa.String(20), nullable=False),
        sa.Column('prediction_type', sa.String(50), nullable=False),
        sa.Column('probability', sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column('confidence', sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['pair_id'], ['pairs.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_predictions_pair_id', 'predictions', ['pair_id'])
    op.create_index('idx_predictions_timestamp', 'predictions', ['timestamp'])

    # signals table
    op.create_table(
        'signals',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('pair_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('strategy_id', sa.String(50), nullable=False),
        sa.Column('signal_type', sa.String(20), nullable=False),
        sa.Column('confidence', sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column('reasons_pro', postgresql.JSON(astext_type=sa.Text()), server_default='[]', nullable=True),
        sa.Column('reasons_contra', postgresql.JSON(astext_type=sa.Text()), server_default='[]', nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['pair_id'], ['pairs.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_signals_pair_id', 'signals', ['pair_id'])
    op.create_index('idx_signals_timestamp', 'signals', ['timestamp'])

    # positions table
    op.create_table(
        'positions',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('pair_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('wallet_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('entry_price', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('entry_amount', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('current_price', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('current_amount', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('stop_loss', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('take_profit', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('status', sa.String(20), server_default='OPEN', nullable=True),
        sa.Column('pnl_usd', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('pnl_percent', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['pair_id'], ['pairs.id'], ),
        sa.ForeignKeyConstraint(['wallet_id'], ['wallets.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_positions_created_at', 'positions', ['created_at'])

    # trades table
    op.create_table(
        'trades',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('position_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('trade_type', sa.String(10), nullable=False),
        sa.Column('price', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('amount', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('fee_usd', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('tx_hash', sa.String(255), nullable=False),
        sa.Column('status', sa.String(20), server_default='PENDING', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['position_id'], ['positions.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tx_hash'),
    )
    op.create_index('idx_trades_created_at', 'trades', ['created_at'])

    # audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('resource', sa.String(50), nullable=False),
        sa.Column('resource_id', sa.String(255), nullable=True),
        sa.Column('details', postgresql.JSON(astext_type=sa.Text()), server_default='{}', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_audit_logs_created_at', 'audit_logs', ['created_at'])

    # bot_state table
    op.create_table(
        'bot_state',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('state', sa.String(20), server_default='STOPPED', nullable=True),
        sa.Column('trading_mode', sa.String(10), server_default='PAPER', nullable=True),
        sa.Column('last_update', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_index('idx_audit_logs_created_at', table_name='audit_logs')
    op.drop_table('audit_logs')
    op.drop_index('idx_trades_created_at', table_name='trades')
    op.drop_table('trades')
    op.drop_index('idx_positions_created_at', table_name='positions')
    op.drop_table('positions')
    op.drop_index('idx_signals_timestamp', table_name='signals')
    op.drop_index('idx_signals_pair_id', table_name='signals')
    op.drop_table('signals')
    op.drop_index('idx_predictions_timestamp', table_name='predictions')
    op.drop_index('idx_predictions_pair_id', table_name='predictions')
    op.drop_table('predictions')
    op.drop_index('idx_features_timestamp', table_name='features')
    op.drop_index('idx_features_pair_id', table_name='features')
    op.drop_table('features')
    op.drop_index('idx_risk_assessments_timestamp', table_name='risk_assessments')
    op.drop_index('idx_risk_assessments_pair_id', table_name='risk_assessments')
    op.drop_table('risk_assessments')
    op.drop_index('idx_market_snapshots_timestamp', table_name='market_snapshots')
    op.drop_index('idx_market_snapshots_pair_id', table_name='market_snapshots')
    op.drop_table('market_snapshots')
    op.drop_table('pairs')
    op.drop_table('wallets')
    op.drop_table('tokens')
    op.drop_table('chains')
    op.drop_index('idx_users_email', table_name='users')
    op.drop_index('idx_users_username', table_name='users')
    op.drop_table('users')
