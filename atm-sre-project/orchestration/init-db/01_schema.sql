-- Users table (auth service)
CREATE TABLE IF NOT EXISTS users (
    id              SERIAL PRIMARY KEY,
    account_number  VARCHAR(20) UNIQUE NOT NULL,
    name            VARCHAR(100) NOT NULL,
    pin_hash        TEXT NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Accounts table (account service)
CREATE TABLE IF NOT EXISTS accounts (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id),
    account_number  VARCHAR(20) UNIQUE NOT NULL,
    balance         NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    currency        VARCHAR(3) NOT NULL DEFAULT 'USD',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Transactions table (transaction service — created here so Phase 1 DB is complete)
CREATE TABLE IF NOT EXISTS transactions (
    id              SERIAL PRIMARY KEY,
    from_account    VARCHAR(20),
    to_account      VARCHAR(20),
    amount          NUMERIC(15, 2) NOT NULL,
    type            VARCHAR(20) NOT NULL, -- deposit | withdraw | transfer
    status          VARCHAR(20) NOT NULL DEFAULT 'success',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Cards table (card-management service)
CREATE TABLE IF NOT EXISTS cards (
    id              SERIAL PRIMARY KEY,
    account_number  VARCHAR(20) NOT NULL REFERENCES accounts(account_number),
    card_number     VARCHAR(19) UNIQUE NOT NULL,
    is_blocked      BOOLEAN NOT NULL DEFAULT FALSE,
    daily_limit     NUMERIC(15, 2) NOT NULL DEFAULT 1000.00,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
