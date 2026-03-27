CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS orders;
CREATE SCHEMA IF NOT EXISTS risk;
CREATE SCHEMA IF NOT EXISTS matching;
CREATE SCHEMA IF NOT EXISTS portfolio;
CREATE SCHEMA IF NOT EXISTS audit;
CREATE SCHEMA IF NOT EXISTS strategy;
CREATE SCHEMA IF NOT EXISTS copilot;

CREATE TABLE IF NOT EXISTS auth.users (
  id UUID PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS auth.accounts (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES auth.users(id),
  name TEXT NOT NULL,
  cash_balance NUMERIC(24, 8) NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS orders.orders (
  id UUID PRIMARY KEY,
  account_id UUID NOT NULL,
  instrument_id TEXT NOT NULL,
  side TEXT NOT NULL,
  order_type TEXT NOT NULL,
  quantity NUMERIC(24, 8) NOT NULL,
  price NUMERIC(24, 8),
  status TEXT NOT NULL,
  source TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS orders.trades (
  id UUID PRIMARY KEY,
  buy_order_id UUID NOT NULL,
  sell_order_id UUID NOT NULL,
  instrument_id TEXT NOT NULL,
  quantity NUMERIC(24, 8) NOT NULL,
  price NUMERIC(24, 8) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS portfolio.positions (
  account_id UUID NOT NULL,
  instrument_id TEXT NOT NULL,
  quantity NUMERIC(24, 8) NOT NULL DEFAULT 0,
  avg_cost NUMERIC(24, 8) NOT NULL DEFAULT 0,
  realized_pnl NUMERIC(24, 8) NOT NULL DEFAULT 0,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (account_id, instrument_id)
);

CREATE TABLE IF NOT EXISTS audit.events (
  id UUID PRIMARY KEY,
  topic TEXT NOT NULL,
  event_key TEXT,
  payload JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit.processed_events (
  id BIGSERIAL PRIMARY KEY,
  service_name TEXT NOT NULL,
  event_id TEXT NOT NULL,
  event_type TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_processed_events_service_event
  ON audit.processed_events (service_name, event_id);

CREATE INDEX IF NOT EXISTS ix_audit_events_topic_created_at
  ON audit.events (topic, created_at);

INSERT INTO auth.users (id, email, password_hash)
VALUES
  ('11111111-1111-1111-1111-111111111111', 'alice@example.com', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f'),
  ('22222222-2222-2222-2222-222222222222', 'bob@example.com', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f')
ON CONFLICT (id) DO NOTHING;

INSERT INTO auth.accounts (id, user_id, name, cash_balance)
VALUES
  ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', '11111111-1111-1111-1111-111111111111', 'Alice Main', 100000.00),
  ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', '22222222-2222-2222-2222-222222222222', 'Bob Main', 100000.00)
ON CONFLICT (id) DO NOTHING;
