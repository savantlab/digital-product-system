import os
from typing import List, Dict
import psycopg
from datetime import datetime, timezone

DB_URL = os.environ.get("DB_URL")

# Entitlement mapping per tier (fallback to env overrides)
DEFAULT_TIER_ENTITLEMENTS = {
    "individual": ["book", "app"],
    "academic": ["book", "app", "lab"],
    "corporate": ["book", "app", "lab"],
    "enterprise": ["book", "app", "lab"],
}

BOOK_DOMAIN = os.environ.get("BOOK_DOMAIN", "").lower()
LAB_DOMAIN = os.environ.get("LAB_DOMAIN", "").lower()
APP_DOMAIN = os.environ.get("APP_DOMAIN", "").lower()


def _conn():
    if not DB_URL:
        raise RuntimeError("DB_URL not configured")
    return psycopg.connect(DB_URL)


def _tier_entitlements() -> Dict[str, List[str]]:
    ent = dict(DEFAULT_TIER_ENTITLEMENTS)
    # Optional per-tier env overrides (comma-separated)
    for tier_key, env_key in (
        ("individual", "ENTITLEMENTS_INDIVIDUAL"),
        ("academic", "ENTITLEMENTS_ACADEMIC"),
        ("corporate", "ENTITLEMENTS_CORPORATE"),
        ("enterprise", "ENTITLEMENTS_ENTERPRISE"),
    ):
        v = os.environ.get(env_key)
        if v:
            ent[tier_key] = [s.strip() for s in v.split(",") if s.strip()]
    return ent


def user_active_licenses(email: str) -> List[Dict]:
    """Return list of active licenses for user email.
    Schema expected from your docs:
      - licenses(id, license_tier, expiration_date, is_active, ...)
      - license_users(license_id, email, ...)
    Adjust column names if needed.
    """
    sql = (
        """
        SELECT l.id, l.license_tier, l.expiration_date, l.is_active
        FROM licenses l
        JOIN license_users u ON u.license_id = l.id
        WHERE LOWER(u.email) = LOWER(%s)
          AND COALESCE(l.is_active, true) = true
          AND (l.expiration_date IS NULL OR l.expiration_date > NOW())
        """
    )
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (email,))
            rows = cur.fetchall()
            return [
                {
                    "id": r[0],
                    "tier": (r[1] or "").lower(),
                    "expires": r[2],
                    "active": r[3],
                }
                for r in rows
            ]


def _scope_for_host(host: str) -> str | None:
    h = (host or "").lower()
    if BOOK_DOMAIN and h == BOOK_DOMAIN:
        return "book"
    if LAB_DOMAIN and h == LAB_DOMAIN:
        return "lab"
    if APP_DOMAIN and h == APP_DOMAIN:
        return "app"
    # Fallback by subdomain prefix
    if h.startswith("book."):
        return "book"
    if h.startswith("lab."):
        return "lab"
    if h.startswith("app."):
        return "app"
    return None


def has_user_entitlement(email: str, host: str) -> bool:
    scope = _scope_for_host(host)
    if not scope:
        return True  # if host not recognized, do not block
    licenses = user_active_licenses(email)
    if not licenses:
        return False
    ent = _tier_entitlements()
    for lic in licenses:
        tier = (lic.get("tier") or "").lower()
        if scope in ent.get(tier, []):
            return True
    return False