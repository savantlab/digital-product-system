-- Email logs table for tracking all sent emails
CREATE TABLE IF NOT EXISTS email_logs (
    id SERIAL PRIMARY KEY,
    email TEXT NOT NULL,
    template TEXT NOT NULL,  -- otp_code, magic_link, welcome, abandoned_cart
    auth_code TEXT,  -- Optional: OTP or auth code for tracking with authentication
    mailgun_id TEXT,  -- Mailgun message ID for tracking
    status TEXT NOT NULL DEFAULT 'sent',  -- sent, delivered, opened, clicked, failed, bounced
    variables JSONB,  -- Email template variables
    metadata JSONB,  -- Additional tracking data (license_id, cart_id, etc.)
    
    -- Event timestamps (updated by Mailgun webhooks)
    sent_at TIMESTAMP,
    delivered_at TIMESTAMP,
    opened_at TIMESTAMP,
    clicked_at TIMESTAMP,
    failed_at TIMESTAMP,
    bounced_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for querying
CREATE INDEX IF NOT EXISTS idx_email_logs_email ON email_logs(LOWER(email));
CREATE INDEX IF NOT EXISTS idx_email_logs_auth_code ON email_logs(auth_code) WHERE auth_code IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_email_logs_mailgun_id ON email_logs(mailgun_id) WHERE mailgun_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_email_logs_template ON email_logs(template);
CREATE INDEX IF NOT EXISTS idx_email_logs_sent_at ON email_logs(sent_at);
CREATE INDEX IF NOT EXISTS idx_email_logs_status ON email_logs(status);
