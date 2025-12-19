"""
Email API for managing and triggering emails with user tracking.
"""
import os
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
import psycopg
from email_mailgun import send_mailgun

email_bp = Blueprint('email', __name__, url_prefix='/api/email')

DB_URL = os.environ.get("DB_URL")


def _conn():
    if not DB_URL:
        raise RuntimeError("DB_URL not configured")
    return psycopg.connect(DB_URL)


@email_bp.route('/send', methods=['POST'])
def send_email():
    """
    Send an email and track it in the database.
    
    POST /api/email/send
    {
        "to": "user@example.com",  // single email
        // OR
        "to": ["user1@example.com", "user2@example.com"],  // batch
        "template": "welcome",  // or "otp_code", "magic_link", "abandoned_cart"
        "variables": {
            "first_name": "John",
            "code": "123456",
            "minutes": 10
        },
        "auth_code": "abc123",  // optional - for tracking with auth flow
        "metadata": {}  // optional - additional tracking data
    }
    """
    data = request.get_json(force=True)
    to_input = data.get('to')
    template = data.get('template', '').strip()
    variables = data.get('variables', {})
    auth_code = data.get('auth_code')
    metadata = data.get('metadata', {})
    
    # Handle single email or list of emails
    if isinstance(to_input, str):
        to_emails = [to_input.strip().lower()]
    elif isinstance(to_input, list):
        to_emails = [email.strip().lower() for email in to_input if email]
    else:
        return jsonify({"ok": False, "error": "to must be a string or array"}), 400
    
    if not to_emails or not template:
        return jsonify({"ok": False, "error": "to and template required"}), 400
    
    # Send emails and track results
    results = []
    
    with _conn() as conn:
        with conn.cursor() as cur:
            for to_email in to_emails:
                # Send email via Mailgun
                try:
                    response = send_mailgun(template, to_email, variables)
                    mailgun_id = response.json().get('id') if response.ok else None
                    status = 'sent' if response.ok else 'failed'
                    error_msg = None
                except Exception as e:
                    mailgun_id = None
                    status = 'failed'
                    error_msg = str(e)
                
                # Track in database
                try:
                    cur.execute("""
                        INSERT INTO email_logs 
                        (email, template, auth_code, mailgun_id, status, variables, metadata, sent_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        to_email,
                        template,
                        auth_code,
                        mailgun_id,
                        status,
                        variables,
                        metadata,
                        datetime.now(timezone.utc)
                    ))
                    email_log_id = cur.fetchone()[0]
                    
                    results.append({
                        "email": to_email,
                        "email_log_id": email_log_id,
                        "status": status,
                        "mailgun_id": mailgun_id,
                        "error": error_msg
                    })
                except Exception as e:
                    results.append({
                        "email": to_email,
                        "status": "error",
                        "error": str(e)
                    })
            
            conn.commit()
    
    # Return single result or batch results
    if len(to_emails) == 1:
        return jsonify({
            "ok": True,
            "email_log_id": results[0].get("email_log_id"),
            "status": results[0]["status"],
            "mailgun_id": results[0].get("mailgun_id")
        })
    else:
        return jsonify({
            "ok": True,
            "batch": True,
            "sent": len([r for r in results if r["status"] == "sent"]),
            "failed": len([r for r in results if r["status"] in ["failed", "error"]]),
            "results": results
        })


@email_bp.route('/status/<int:email_log_id>', methods=['GET'])
def get_email_status(email_log_id):
    """
    Get the status of a sent email.
    
    GET /api/email/status/123
    """
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, email, template, auth_code, status, 
                           sent_at, delivered_at, opened_at, clicked_at, failed_at
                    FROM email_logs
                    WHERE id = %s
                """, (email_log_id,))
                row = cur.fetchone()
                
                if not row:
                    return jsonify({"ok": False, "error": "Email log not found"}), 404
                
                return jsonify({
                    "ok": True,
                    "email_log": {
                        "id": row[0],
                        "email": row[1],
                        "template": row[2],
                        "auth_code": row[3],
                        "status": row[4],
                        "sent_at": row[5].isoformat() if row[5] else None,
                        "delivered_at": row[6].isoformat() if row[6] else None,
                        "opened_at": row[7].isoformat() if row[7] else None,
                        "clicked_at": row[8].isoformat() if row[8] else None,
                        "failed_at": row[9].isoformat() if row[9] else None
                    }
                })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@email_bp.route('/history/<email>', methods=['GET'])
def get_email_history(email):
    """
    Get email history for a user by email address.
    
    GET /api/email/history/user@example.com?limit=50
    """
    email = email.strip().lower()
    limit = min(int(request.args.get('limit', 50)), 200)
    
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, template, auth_code, status, sent_at, delivered_at
                    FROM email_logs
                    WHERE LOWER(email) = %s
                    ORDER BY sent_at DESC
                    LIMIT %s
                """, (email, limit))
                rows = cur.fetchall()
                
                return jsonify({
                    "ok": True,
                    "emails": [
                        {
                            "id": r[0],
                            "template": r[1],
                            "auth_code": r[2],
                            "status": r[3],
                            "sent_at": r[4].isoformat() if r[4] else None,
                            "delivered_at": r[5].isoformat() if r[5] else None
                        }
                        for r in rows
                    ]
                })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@email_bp.route('/user/<email>', methods=['GET'])
def get_user_by_email(email):
    """
    Get user information by email address (from licenses).
    
    GET /api/email/user/user@example.com
    """
    email = email.strip().lower()
    
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                # Get licenses for this user
                cur.execute("""
                    SELECT DISTINCT l.id, l.license_tier, l.owner_email, 
                           l.is_active, l.expiration_date, l.created_at
                    FROM licenses l
                    JOIN license_users u ON u.license_id = l.id
                    WHERE LOWER(u.email) = %s
                    ORDER BY l.created_at DESC
                """, (email,))
                licenses = cur.fetchall()
                
                # Get recent auth activity (from email logs)
                cur.execute("""
                    SELECT template, auth_code, sent_at
                    FROM email_logs
                    WHERE LOWER(email) = %s AND auth_code IS NOT NULL
                    ORDER BY sent_at DESC
                    LIMIT 5
                """, (email,))
                auth_history = cur.fetchall()
                
                return jsonify({
                    "ok": True,
                    "user": {
                        "email": email,
                        "licenses": [
                            {
                                "id": l[0],
                                "tier": l[1],
                                "owner_email": l[2],
                                "is_active": l[3],
                                "expires": l[4].isoformat() if l[4] else None,
                                "created_at": l[5].isoformat() if l[5] else None
                            }
                            for l in licenses
                        ],
                        "recent_auth": [
                            {
                                "template": a[0],
                                "auth_code": a[1],
                                "sent_at": a[2].isoformat() if a[2] else None
                            }
                            for a in auth_history
                        ]
                    }
                })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@email_bp.route('/trigger/welcome', methods=['POST'])
def trigger_welcome_email():
    """
    Trigger welcome email after purchase.
    
    POST /api/email/trigger/welcome
    {
        "email": "user@example.com",
        "first_name": "John",
        "license_id": 123
    }
    """
    data = request.get_json(force=True)
    email = data.get('email', '').strip().lower()
    first_name = data.get('first_name', '')
    license_id = data.get('license_id')
    
    if not email:
        return jsonify({"ok": False, "error": "email required"}), 400
    
    # Get license details
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT license_tier FROM licenses WHERE id = %s
                """, (license_id,))
                row = cur.fetchone()
                tier = row[0] if row else 'individual'
    except Exception:
        tier = 'individual'
    
    # Send welcome email
    variables = {
        "first_name": first_name,
        "book_domain": os.environ.get("BOOK_DOMAIN", ""),
        "lab_domain": os.environ.get("LAB_DOMAIN", ""),
        "app_domain": os.environ.get("APP_DOMAIN", "")
    }
    
    try:
        response = send_mailgun("welcome", email, variables)
        
        # Log email
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO email_logs 
                    (email, template, mailgun_id, status, variables, metadata, sent_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    email,
                    'welcome',
                    response.json().get('id') if response.ok else None,
                    'sent' if response.ok else 'failed',
                    variables,
                    {"license_id": license_id, "tier": tier},
                    datetime.now(timezone.utc)
                ))
                conn.commit()
        
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@email_bp.route('/trigger/abandoned-cart', methods=['POST'])
def trigger_abandoned_cart_email():
    """
    Trigger abandoned cart email.
    
    POST /api/email/trigger/abandoned-cart
    {
        "email": "user@example.com",
        "first_name": "John",
        "tier": "individual",
        "cart_id": "abc123"
    }
    """
    data = request.get_json(force=True)
    email = data.get('email', '').strip().lower()
    first_name = data.get('first_name', '')
    tier = data.get('tier', 'individual')
    cart_id = data.get('cart_id', '')
    
    if not email:
        return jsonify({"ok": False, "error": "email required"}), 400
    
    # Build resume URL
    resume_url = f"https://{os.environ.get('EVENTS_DOMAIN', '')}/checkout?cart={cart_id}"
    
    variables = {
        "first_name": first_name,
        "tier": tier,
        "resume_url": resume_url
    }
    
    try:
        response = send_mailgun("abandoned_cart", email, variables)
        
        # Log email
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO email_logs 
                    (email, template, mailgun_id, status, variables, metadata, sent_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    email,
                    'abandoned_cart',
                    response.json().get('id') if response.ok else None,
                    'sent' if response.ok else 'failed',
                    variables,
                    {"tier": tier, "cart_id": cart_id},
                    datetime.now(timezone.utc)
                ))
                conn.commit()
        
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
