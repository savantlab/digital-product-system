-- Flog (Fraud Blog) articles table
CREATE TABLE IF NOT EXISTS flog_articles (
    id SERIAL PRIMARY KEY,
    slug TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    excerpt TEXT,
    content TEXT NOT NULL,
    author TEXT DEFAULT 'Anonymous',
    tags TEXT[],
    is_published BOOLEAN DEFAULT false,
    published_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_flog_slug ON flog_articles(slug);
CREATE INDEX IF NOT EXISTS idx_flog_published ON flog_articles(is_published, published_at DESC) WHERE is_published = true;
CREATE INDEX IF NOT EXISTS idx_flog_created ON flog_articles(created_at DESC);

-- Comments
COMMENT ON TABLE flog_articles IS 'Fraud blog articles exposing academic deception';
COMMENT ON COLUMN flog_articles.slug IS 'URL-friendly identifier for the article';
COMMENT ON COLUMN flog_articles.excerpt IS 'Brief summary/preview of the article';
COMMENT ON COLUMN flog_articles.content IS 'Full article content (markdown supported)';
COMMENT ON COLUMN flog_articles.tags IS 'Array of tags for categorization (e.g. fraud, peterson, harvard)';
