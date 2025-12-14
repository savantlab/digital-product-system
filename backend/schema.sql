-- Licenses table
CREATE TABLE IF NOT EXISTS licenses (
    id SERIAL PRIMARY KEY,
    license_tier TEXT NOT NULL CHECK (license_tier IN ('individual', 'academic', 'corporate', 'government', 'nonprofit')),
    order_id TEXT UNIQUE,
    owner_email TEXT NOT NULL,
    seat_limit INTEGER,  -- NULL = unlimited, number = hard limit for nonprofit
    is_active BOOLEAN DEFAULT true,
    expiration_date TIMESTAMP,  -- NULL = lifetime
    cohort_name TEXT,  -- Optional for academic licenses
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_licenses_order_id ON licenses(order_id);
CREATE INDEX IF NOT EXISTS idx_licenses_owner_email ON licenses(LOWER(owner_email));

-- License users table (many-to-many relationship)
CREATE TABLE IF NOT EXISTS license_users (
    license_id INTEGER NOT NULL REFERENCES licenses(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (license_id, email)
);

CREATE INDEX IF NOT EXISTS idx_license_users_email ON license_users(LOWER(email));

-- Access tokens table (for one-time auto-login links)
CREATE TABLE IF NOT EXISTS access_tokens (
    token TEXT PRIMARY KEY,
    email TEXT NOT NULL,
    license_id INTEGER REFERENCES licenses(id) ON DELETE CASCADE,
    used_at TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_access_tokens_email ON access_tokens(LOWER(email));
CREATE INDEX IF NOT EXISTS idx_access_tokens_expires ON access_tokens(expires_at);
