-- Terms of Use content management table
CREATE TABLE IF NOT EXISTS tou_content (
    id SERIAL PRIMARY KEY,
    version INTEGER NOT NULL UNIQUE,
    content JSONB NOT NULL,  -- Structured sections of the TOU
    is_active BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by TEXT  -- Admin email who created/updated
);

-- Index for finding active version
CREATE INDEX IF NOT EXISTS idx_tou_content_active ON tou_content(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_tou_content_version ON tou_content(version DESC);

-- User acceptance tracking
CREATE TABLE IF NOT EXISTS tou_acceptances (
    id SERIAL PRIMARY KEY,
    email TEXT NOT NULL,
    tou_version INTEGER NOT NULL REFERENCES tou_content(version),
    accepted_at TIMESTAMP DEFAULT NOW(),
    ip_address TEXT,
    user_agent TEXT
);

CREATE INDEX IF NOT EXISTS idx_tou_acceptances_email ON tou_acceptances(LOWER(email));
CREATE INDEX IF NOT EXISTS idx_tou_acceptances_version ON tou_acceptances(tou_version);

-- Ensure only one active version at a time
CREATE UNIQUE INDEX IF NOT EXISTS idx_tou_content_single_active 
    ON tou_content(is_active) WHERE is_active = true;

-- Insert default TOU content (version 1)
INSERT INTO tou_content (version, content, is_active, created_by) VALUES (
    1,
    '{
        "sections": [
            {
                "title": "1. Acceptance of Terms",
                "content": "By accessing this course, you agree to be bound by these Terms of Use. If you do not agree to these terms, you may not access or use this course."
            },
            {
                "title": "2. Educational Purpose",
                "content": "This course is provided solely for educational, academic, and research purposes. The content analyzes extremist ideologies to promote understanding of how such ideologies function and spread."
            },
            {
                "title": "3. Content Disclaimer",
                "content": "This course contains analysis of:\n• Nazi terrorism and mass violence\n• Supremacist ideologies (white supremacy, male supremacy)\n• Antisemitic conspiracy theories\n• Violent extremist manifestos\n\nNothing in this course endorses, promotes, or supports extremist views, violence, or discrimination of any kind."
            },
            {
                "title": "4. Age Restriction",
                "content": "You must be at least 18 years old to access this course. This content is intended for mature audiences capable of critical analysis."
            },
            {
                "title": "5. Prohibited Use",
                "content": "You agree NOT to:\n• Use this course content to promote, encourage, or engage in extremist activities\n• Reproduce or distribute course materials for purposes other than personal education\n• Misrepresent the course content or its conclusions\n• Use the course to harass, threaten, or harm others"
            },
            {
                "title": "6. Intellectual Property",
                "content": "All course content is protected by copyright. Quoted materials from external sources are used under fair use doctrine for purposes of criticism, commentary, and education."
            },
            {
                "title": "7. No Liability",
                "content": "The course provider makes no warranties about the completeness, reliability, or accuracy of this information. The course provider is not liable for any consequences arising from use of this course."
            },
            {
                "title": "8. Modification of Terms",
                "content": "These Terms of Use may be updated at any time. Continued use of the course constitutes acceptance of updated terms."
            },
            {
                "title": "9. Contact",
                "content": "For questions about these terms, contact: support@scideology.app"
            }
        ],
        "agreement_text": "I am at least 18 years old, I have read and understood these Terms of Use, and I agree to be bound by them. I understand this course analyzes extremist content for educational purposes only."
    }'::jsonb,
    true,
    'system'
) ON CONFLICT (version) DO NOTHING;
