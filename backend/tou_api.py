"""
Terms of Use API endpoints for managing TOU content.
"""
import os
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
import psycopg

DB_URL = os.environ.get("DB_URL")

tou_bp = Blueprint('tou', __name__, url_prefix='/api/tou')


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


@tou_bp.route('', methods=['GET'])
def get_active_tou():
    """
    GET /api/tou
    Returns the active Terms of Use content.
    """
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT version, content, created_at, updated_at
                    FROM tou_content
                    WHERE is_active = true
                    LIMIT 1
                """)
                row = cur.fetchone()
                
                if not row:
                    return cors((jsonify({
                        "ok": False,
                        "error": "No active TOU found"
                    }), 404))
                
                return cors(jsonify({
                    "ok": True,
                    "data": {
                        "version": row[0],
                        "content": row[1],
                        "created_at": row[2].isoformat() if row[2] else None,
                        "updated_at": row[3].isoformat() if row[3] else None
                    }
                }))
    except Exception as e:
        return cors((jsonify({
            "ok": False,
            "error": str(e)
        }), 500))


@tou_bp.route('/version/<int:version>', methods=['GET'])
def get_tou_version(version):
    """
    GET /api/tou/version/<version>
    Returns a specific version of the Terms of Use.
    """
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT version, content, is_active, created_at, updated_at, created_by
                    FROM tou_content
                    WHERE version = %s
                """, (version,))
                row = cur.fetchone()
                
                if not row:
                    return cors((jsonify({
                        "ok": False,
                        "error": f"Version {version} not found"
                    }), 404))
                
                return cors(jsonify({
                    "ok": True,
                    "data": {
                        "version": row[0],
                        "content": row[1],
                        "is_active": row[2],
                        "created_at": row[3].isoformat() if row[3] else None,
                        "updated_at": row[4].isoformat() if row[4] else None,
                        "created_by": row[5]
                    }
                }))
    except Exception as e:
        return cors((jsonify({
            "ok": False,
            "error": str(e)
        }), 500))


@tou_bp.route('', methods=['POST'])
def create_tou():
    """
    POST /api/tou
    Creates a new version of Terms of Use.
    
    Request body:
    {
        "content": {
            "sections": [...],
            "agreement_text": "..."
        },
        "created_by": "admin@example.com",
        "set_active": false  // Optional: immediately activate this version
    }
    
    Returns the newly created version number.
    """
    try:
        data = request.get_json(force=True)
        content = data.get("content")
        created_by = data.get("created_by", "unknown")
        set_active = data.get("set_active", False)
        
        if not content:
            return cors((jsonify({
                "ok": False,
                "error": "content is required"
            }), 400))
        
        # Validate content structure
        if not isinstance(content, dict):
            return cors((jsonify({
                "ok": False,
                "error": "content must be a JSON object"
            }), 400))
        
        if "sections" not in content or not isinstance(content["sections"], list):
            return cors((jsonify({
                "ok": False,
                "error": "content must contain a 'sections' array"
            }), 400))
        
        with _conn() as conn:
            with conn.cursor() as cur:
                # Get next version number
                cur.execute("SELECT COALESCE(MAX(version), 0) + 1 FROM tou_content")
                next_version = cur.fetchone()[0]
                
                # If set_active is True, deactivate all other versions
                if set_active:
                    cur.execute("UPDATE tou_content SET is_active = false WHERE is_active = true")
                
                # Insert new version
                cur.execute("""
                    INSERT INTO tou_content (version, content, is_active, created_by, updated_at)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id, version, created_at
                """, (
                    next_version,
                    psycopg.types.json.Jsonb(content),
                    set_active,
                    created_by,
                    datetime.now(timezone.utc)
                ))
                
                result = cur.fetchone()
                conn.commit()
                
                return cors(jsonify({
                    "ok": True,
                    "data": {
                        "id": result[0],
                        "version": result[1],
                        "is_active": set_active,
                        "created_at": result[2].isoformat() if result[2] else None
                    }
                }))
                
    except Exception as e:
        return cors((jsonify({
            "ok": False,
            "error": str(e)
        }), 500))


@tou_bp.route('/version/<int:version>', methods=['PUT'])
def update_tou(version):
    """
    PUT /api/tou/version/<version>
    Updates an existing TOU version's content or activation status.
    
    Request body:
    {
        "content": { ... },  // Optional: new content
        "set_active": true,  // Optional: activate/deactivate this version
        "updated_by": "admin@example.com"
    }
    """
    try:
        data = request.get_json(force=True)
        content = data.get("content")
        set_active = data.get("set_active")
        updated_by = data.get("updated_by", "unknown")
        
        with _conn() as conn:
            with conn.cursor() as cur:
                # Check if version exists
                cur.execute("SELECT id FROM tou_content WHERE version = %s", (version,))
                if not cur.fetchone():
                    return cors((jsonify({
                        "ok": False,
                        "error": f"Version {version} not found"
                    }), 404))
                
                updates = []
                params = []
                
                if content is not None:
                    # Validate content structure
                    if not isinstance(content, dict):
                        return cors((jsonify({
                            "ok": False,
                            "error": "content must be a JSON object"
                        }), 400))
                    
                    if "sections" not in content or not isinstance(content["sections"], list):
                        return cors((jsonify({
                            "ok": False,
                            "error": "content must contain a 'sections' array"
                        }), 400))
                    
                    updates.append("content = %s")
                    params.append(psycopg.types.json.Jsonb(content))
                
                if set_active is not None:
                    # If activating this version, deactivate all others
                    if set_active:
                        cur.execute("UPDATE tou_content SET is_active = false WHERE is_active = true AND version != %s", (version,))
                    
                    updates.append("is_active = %s")
                    params.append(set_active)
                
                if not updates:
                    return cors((jsonify({
                        "ok": False,
                        "error": "No updates provided"
                    }), 400))
                
                # Add updated timestamp and updated_by
                updates.append("updated_at = %s")
                params.append(datetime.now(timezone.utc))
                
                updates.append("created_by = %s")  # Using created_by field to track last updater
                params.append(updated_by)
                
                # Add version to params
                params.append(version)
                
                # Execute update
                sql = f"UPDATE tou_content SET {', '.join(updates)} WHERE version = %s RETURNING version, is_active, updated_at"
                cur.execute(sql, params)
                result = cur.fetchone()
                conn.commit()
                
                return cors(jsonify({
                    "ok": True,
                    "data": {
                        "version": result[0],
                        "is_active": result[1],
                        "updated_at": result[2].isoformat() if result[2] else None
                    }
                }))
                
    except Exception as e:
        return cors((jsonify({
            "ok": False,
            "error": str(e)
        }), 500))


@tou_bp.route('/accept', methods=['POST'])
def accept_tou():
    """
    POST /api/tou/accept
    Records user's acceptance of the Terms of Use.
    
    Request body:
    {
        "email": "user@example.com",
        "version": 1
    }
    """
    try:
        data = request.get_json(force=True)
        email = (data.get("email") or "").strip().lower()
        version = data.get("version")
        
        if not email or not version:
            return cors((jsonify({
                "ok": False,
                "error": "email and version are required"
            }), 400))
        
        # Get user's IP and user agent
        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
        user_agent = request.headers.get('User-Agent', '')
        
        with _conn() as conn:
            with conn.cursor() as cur:
                # Verify version exists
                cur.execute("SELECT version FROM tou_content WHERE version = %s", (version,))
                if not cur.fetchone():
                    return cors((jsonify({
                        "ok": False,
                        "error": f"Version {version} does not exist"
                    }), 404))
                
                # Record acceptance
                cur.execute("""
                    INSERT INTO tou_acceptances (email, tou_version, ip_address, user_agent)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id, accepted_at
                """, (email, version, ip_address, user_agent))
                
                result = cur.fetchone()
                conn.commit()
                
                return cors(jsonify({
                    "ok": True,
                    "data": {
                        "id": result[0],
                        "accepted_at": result[1].isoformat() if result[1] else None
                    }
                }))
                
    except Exception as e:
        return cors((jsonify({
            "ok": False,
            "error": str(e)
        }), 500))


@tou_bp.route('/history', methods=['GET'])
def get_tou_history():
    """
    GET /api/tou/history
    Returns all TOU versions ordered by version number (newest first).
    """
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT version, is_active, created_at, updated_at, created_by
                    FROM tou_content
                    ORDER BY version DESC
                """)
                rows = cur.fetchall()
                
                return cors(jsonify({
                    "ok": True,
                    "data": [
                        {
                            "version": row[0],
                            "is_active": row[1],
                            "created_at": row[2].isoformat() if row[2] else None,
                            "updated_at": row[3].isoformat() if row[3] else None,
                            "created_by": row[4]
                        }
                        for row in rows
                    ]
                }))
    except Exception as e:
        return cors((jsonify({
            "ok": False,
            "error": str(e)
        }), 500))
