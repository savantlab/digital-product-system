"""
Flog (Fraud Blog) API endpoints for managing articles.
"""
import os
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
import psycopg

DB_URL = os.environ.get("DB_URL")

flog_bp = Blueprint('flog', __name__, url_prefix='/api/flog')


def _conn():
    if not DB_URL:
        raise RuntimeError("DB_URL not configured")
    return psycopg.connect(DB_URL)


def cors(resp):
    """Add CORS headers to response"""
    origin = request.headers.get("Origin", "*")
    allowed_origins = os.environ.get("ALLOWED_ORIGINS", "*")
    if isinstance(resp, tuple):
        response, status = resp
        response.headers["Access-Control-Allow-Origin"] = (
            origin if allowed_origins == "*" or origin in allowed_origins.split(",") else "null"
        )
        response.headers["Vary"] = "Origin"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return response, status
    else:
        resp.headers["Access-Control-Allow-Origin"] = (
            origin if allowed_origins == "*" or origin in allowed_origins.split(",") else "null"
        )
        resp.headers["Vary"] = "Origin"
        resp.headers["Access-Control-Allow-Credentials"] = "true"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return resp


@flog_bp.route('/articles', methods=['GET'])
def get_articles():
    """
    GET /api/flog/articles
    Returns all published Flog articles ordered by publish date (newest first).
    
    Optional query params:
    - limit: max number of articles to return (default: 50)
    - published: true/false to filter by published status (default: true)
    """
    try:
        limit = int(request.args.get('limit', 50))
        published_only = request.args.get('published', 'true').lower() == 'true'
        
        with _conn() as conn:
            with conn.cursor() as cur:
                if published_only:
                    cur.execute("""
                        SELECT id, slug, title, excerpt, content, author, tags, 
                               published_at, created_at, updated_at
                        FROM flog_articles
                        WHERE is_published = true AND published_at <= NOW()
                        ORDER BY published_at DESC
                        LIMIT %s
                    """, (limit,))
                else:
                    cur.execute("""
                        SELECT id, slug, title, excerpt, content, author, tags, 
                               is_published, published_at, created_at, updated_at
                        FROM flog_articles
                        ORDER BY created_at DESC
                        LIMIT %s
                    """, (limit,))
                
                rows = cur.fetchall()
                
                articles = []
                for row in rows:
                    article = {
                        "id": row[0],
                        "slug": row[1],
                        "title": row[2],
                        "excerpt": row[3],
                        "content": row[4],
                        "author": row[5],
                        "tags": row[6],
                        "published_at": row[7].isoformat() if row[7] else None,
                        "created_at": row[8].isoformat() if row[8] else None,
                        "updated_at": row[9].isoformat() if row[9] else None
                    }
                    if not published_only and len(row) > 10:
                        article["is_published"] = row[7]
                    articles.append(article)
                
                return cors(jsonify({
                    "ok": True,
                    "articles": articles
                }))
    except Exception as e:
        return cors((jsonify({
            "ok": False,
            "error": str(e)
        }), 500))


@flog_bp.route('/articles/<slug>', methods=['GET'])
def get_article(slug):
    """
    GET /api/flog/articles/<slug>
    Returns a specific article by slug.
    """
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, slug, title, excerpt, content, author, tags, 
                           published_at, created_at, updated_at
                    FROM flog_articles
                    WHERE slug = %s AND is_published = true
                """, (slug,))
                
                row = cur.fetchone()
                
                if not row:
                    return cors((jsonify({
                        "ok": False,
                        "error": "Article not found"
                    }), 404))
                
                article = {
                    "id": row[0],
                    "slug": row[1],
                    "title": row[2],
                    "excerpt": row[3],
                    "content": row[4],
                    "author": row[5],
                    "tags": row[6],
                    "published_at": row[7].isoformat() if row[7] else None,
                    "created_at": row[8].isoformat() if row[8] else None,
                    "updated_at": row[9].isoformat() if row[9] else None
                }
                
                return cors(jsonify({
                    "ok": True,
                    "article": article
                }))
    except Exception as e:
        return cors((jsonify({
            "ok": False,
            "error": str(e)
        }), 500))


@flog_bp.route('/articles', methods=['POST'])
def create_article():
    """
    POST /api/flog/articles
    Creates a new Flog article.
    
    Request body:
    {
        "title": "Article Title",
        "slug": "article-slug",  // optional, auto-generated from title if not provided
        "excerpt": "Brief summary...",
        "content": "Full article content (markdown supported)",
        "author": "Author Name",
        "tags": ["fraud", "peterson", "harvard"],  // optional
        "is_published": false,  // optional, default false
        "published_at": "2024-01-01T00:00:00Z"  // optional, defaults to now if is_published=true
    }
    """
    try:
        data = request.get_json(force=True)
        
        title = data.get("title")
        slug = data.get("slug")
        excerpt = data.get("excerpt")
        content = data.get("content")
        author = data.get("author", "Anonymous")
        tags = data.get("tags", [])
        is_published = data.get("is_published", False)
        published_at = data.get("published_at")
        
        if not title or not content:
            return cors((jsonify({
                "ok": False,
                "error": "title and content are required"
            }), 400))
        
        # Auto-generate slug if not provided
        if not slug:
            slug = title.lower().replace(" ", "-").replace("'", "")
            # Remove special characters
            slug = "".join(c for c in slug if c.isalnum() or c == "-")
        
        # Set published_at to now if publishing and no date provided
        if is_published and not published_at:
            published_at = datetime.now(timezone.utc)
        
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO flog_articles 
                    (slug, title, excerpt, content, author, tags, is_published, published_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, slug, created_at
                """, (slug, title, excerpt, content, author, tags, is_published, published_at))
                
                result = cur.fetchone()
                conn.commit()
                
                return cors(jsonify({
                    "ok": True,
                    "article": {
                        "id": result[0],
                        "slug": result[1],
                        "created_at": result[2].isoformat() if result[2] else None
                    }
                }))
                
    except Exception as e:
        return cors((jsonify({
            "ok": False,
            "error": str(e)
        }), 500))


@flog_bp.route('/articles/<int:article_id>', methods=['PUT'])
def update_article(article_id):
    """
    PUT /api/flog/articles/<article_id>
    Updates an existing article.
    
    Request body: Same as POST, all fields optional
    """
    try:
        data = request.get_json(force=True)
        
        with _conn() as conn:
            with conn.cursor() as cur:
                # Check if article exists
                cur.execute("SELECT id FROM flog_articles WHERE id = %s", (article_id,))
                if not cur.fetchone():
                    return cors((jsonify({
                        "ok": False,
                        "error": "Article not found"
                    }), 404))
                
                updates = []
                params = []
                
                if "title" in data:
                    updates.append("title = %s")
                    params.append(data["title"])
                
                if "slug" in data:
                    updates.append("slug = %s")
                    params.append(data["slug"])
                
                if "excerpt" in data:
                    updates.append("excerpt = %s")
                    params.append(data["excerpt"])
                
                if "content" in data:
                    updates.append("content = %s")
                    params.append(data["content"])
                
                if "author" in data:
                    updates.append("author = %s")
                    params.append(data["author"])
                
                if "tags" in data:
                    updates.append("tags = %s")
                    params.append(data["tags"])
                
                if "is_published" in data:
                    updates.append("is_published = %s")
                    params.append(data["is_published"])
                    
                    # Set published_at when publishing
                    if data["is_published"] and "published_at" not in data:
                        updates.append("published_at = %s")
                        params.append(datetime.now(timezone.utc))
                
                if "published_at" in data:
                    updates.append("published_at = %s")
                    params.append(data["published_at"])
                
                if not updates:
                    return cors((jsonify({
                        "ok": False,
                        "error": "No updates provided"
                    }), 400))
                
                updates.append("updated_at = %s")
                params.append(datetime.now(timezone.utc))
                params.append(article_id)
                
                sql = f"UPDATE flog_articles SET {', '.join(updates)} WHERE id = %s RETURNING slug, updated_at"
                cur.execute(sql, params)
                result = cur.fetchone()
                conn.commit()
                
                return cors(jsonify({
                    "ok": True,
                    "article": {
                        "id": article_id,
                        "slug": result[0],
                        "updated_at": result[1].isoformat() if result[1] else None
                    }
                }))
                
    except Exception as e:
        return cors((jsonify({
            "ok": False,
            "error": str(e)
        }), 500))


@flog_bp.route('/articles/<int:article_id>', methods=['DELETE'])
def delete_article(article_id):
    """
    DELETE /api/flog/articles/<article_id>
    Deletes an article.
    """
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM flog_articles WHERE id = %s RETURNING id", (article_id,))
                result = cur.fetchone()
                
                if not result:
                    return cors((jsonify({
                        "ok": False,
                        "error": "Article not found"
                    }), 404))
                
                conn.commit()
                
                return cors(jsonify({
                    "ok": True,
                    "message": "Article deleted"
                }))
                
    except Exception as e:
        return cors((jsonify({
            "ok": False,
            "error": str(e)
        }), 500))
