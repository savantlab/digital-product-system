import os
import uuid
import json
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, jsonify
import requests

app = Flask(__name__)

# Admin API key
ADMIN_API_KEY = os.environ.get("ADMIN_API_KEY", "change-me-in-production")

# Product metadata file
PRODUCT_DATA_FILE = Path("/data/product_data.json")
PRODUCT_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

# Pricing (in cents)
PRICE_INDIVIDUAL = int(os.environ.get("PRICE_INDIVIDUAL", "1499"))
PRICE_ACADEMIC   = int(os.environ.get("PRICE_ACADEMIC",   "49999"))
PRICE_CORPORATE  = int(os.environ.get("PRICE_CORPORATE",  "99999"))
PRICE_GOVERNMENT = int(os.environ.get("PRICE_GOVERNMENT", "49999"))
PRICE_NONPROFIT_PER_USER = int(os.environ.get("PRICE_NONPROFIT_PER_USER", "999"))
NONPROFIT_MIN_USERS = int(os.environ.get("NONPROFIT_MIN_USERS", "10"))
CURRENCY = os.environ.get("CURRENCY", "USD")

# Square
SQUARE_ACCESS_TOKEN = os.environ.get("SQUARE_ACCESS_TOKEN")
SQUARE_LOCATION_ID  = os.environ.get("SQUARE_LOCATION_ID")
SQUARE_BASE         = os.environ.get("SQUARE_BASE", "https://connect.squareup.com")

STORE_BASE_URL      = os.environ.get("STORE_BASE_URL", "https://scideology.app")

# Load product data from file or defaults
def load_product_data():
    if PRODUCT_DATA_FILE.exists():
        with open(PRODUCT_DATA_FILE) as f:
            return json.load(f)
    return {
        "title": "Parallel Critiques — Analyzing Rhetorical Extremism",
        "description": "Purchase access to the complete text analysis book and interactive notebooks.",
        "hero_image": None,
        "gallery_images": [],
        "tiers": {
            "individual": {"name": "Individual", "price": PRICE_INDIVIDUAL, "description": "Personal use (1 user)."},
            "academic": {"name": "Academic/Educational", "price": PRICE_ACADEMIC, "description": "One course or cohort. Unlimited students. Upload roster after purchase."},
            "corporate": {"name": "Corporate/Agency", "price": PRICE_CORPORATE, "description": "Unlimited team members."},
            "government": {"name": "Government", "price": PRICE_GOVERNMENT, "description": "Unlimited users per agency."},
            "nonprofit": {"name": "Non-Profit", "price": PRICE_NONPROFIT_PER_USER * NONPROFIT_MIN_USERS, "description": f"${PRICE_NONPROFIT_PER_USER/100:.2f} per user. Minimum {NONPROFIT_MIN_USERS} users."},
        }
    }

def save_product_data(data):
    with open(PRODUCT_DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

PRODUCT_DATA = load_product_data()
TIERS = PRODUCT_DATA["tiers"]

@app.get("/")
def product():
    return render_template("product.html", product=PRODUCT_DATA, tiers=TIERS)

@app.post("/checkout")
def checkout():
    tier_key = (request.form.get("tier") or "individual").lower()
    buyer_email = (request.form.get("email") or "").strip()
    if tier_key not in TIERS:
        tier_key = "individual"
    tier = TIERS[tier_key]

    if not (SQUARE_ACCESS_TOKEN and SQUARE_LOCATION_ID):
        # Dev mode fallback: simulate success
        return redirect(url_for("confirmation", status="simulated", tier=tier_key))

    headers = {
        "Authorization": f"Bearer {SQUARE_ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "Square-Version": os.environ.get("SQUARE_VERSION", "2024-09-26"),
    }

    idempotency_key = str(uuid.uuid4())
    body = {
        "idempotency_key": idempotency_key,
        "order": {
            "location_id": SQUARE_LOCATION_ID,
            "line_items": [
                {
                    "name": f"{PRODUCT_DATA['title']} — {tier['name']} License",
                    "quantity": "1",
                    "base_price_money": {"amount": tier["price"], "currency": CURRENCY},
                }
            ],
        },
        "checkout_options": {
            "redirect_url": f"{STORE_BASE_URL}/confirmation",
            "ask_for_shipping_address": False,
            "enable_guest_checkout": True,
        },
    }
    if buyer_email:
        body["pre_populated_data"] = {"buyer_email": buyer_email}

    try:
        resp = requests.post(
            f"{SQUARE_BASE}/v2/online-checkout/payment-links",
            headers=headers,
            json=body,
            timeout=15,
        )
        data = resp.json()
        url = data.get("payment_link", {}).get("url")
        if resp.status_code == 200 and url:
            return redirect(url)
        return redirect(url_for("confirmation", status="error", reason=data.get("errors", [{}])[0].get("detail", "checkout_error")))
    except Exception:
        return redirect(url_for("confirmation", status="error", reason="network_error"))

# Admin API - require API key
def require_admin():
    key = request.headers.get("X-Admin-Key") or request.args.get("api_key")
    if key != ADMIN_API_KEY:
        return jsonify({"error": "unauthorized"}), 401
    return None

@app.post("/api/admin/product")
def update_product():
    err = require_admin()
    if err:
        return err
    
    global PRODUCT_DATA, TIERS
    data = request.get_json() or {}
    
    if "title" in data:
        PRODUCT_DATA["title"] = data["title"]
    if "description" in data:
        PRODUCT_DATA["description"] = data["description"]
    if "hero_image" in data:
        PRODUCT_DATA["hero_image"] = data["hero_image"]
    if "gallery_images" in data:
        PRODUCT_DATA["gallery_images"] = data["gallery_images"]
    
    save_product_data(PRODUCT_DATA)
    return jsonify({"status": "updated", "product": PRODUCT_DATA})

@app.post("/api/admin/product/title")
def update_title():
    err = require_admin()
    if err:
        return err
    
    global PRODUCT_DATA
    data = request.get_json() or {}
    PRODUCT_DATA["title"] = data.get("value", PRODUCT_DATA["title"])
    save_product_data(PRODUCT_DATA)
    return jsonify({"status": "updated", "title": PRODUCT_DATA["title"]})

@app.post("/api/admin/product/description")
def update_description():
    err = require_admin()
    if err:
        return err
    
    global PRODUCT_DATA
    data = request.get_json() or {}
    PRODUCT_DATA["description"] = data.get("value", PRODUCT_DATA["description"])
    save_product_data(PRODUCT_DATA)
    return jsonify({"status": "updated", "description": PRODUCT_DATA["description"]})

@app.post("/api/admin/product/hero_image")
def update_hero_image():
    err = require_admin()
    if err:
        return err
    
    global PRODUCT_DATA
    data = request.get_json() or {}
    PRODUCT_DATA["hero_image"] = data.get("url")
    save_product_data(PRODUCT_DATA)
    return jsonify({"status": "updated", "hero_image": PRODUCT_DATA["hero_image"]})

@app.post("/api/admin/product/gallery_images")
def update_gallery():
    err = require_admin()
    if err:
        return err
    
    global PRODUCT_DATA
    data = request.get_json() or {}
    PRODUCT_DATA["gallery_images"] = data.get("images", [])
    save_product_data(PRODUCT_DATA)
    return jsonify({"status": "updated", "gallery_images": PRODUCT_DATA["gallery_images"]})

@app.post("/api/admin/tiers/<tier_key>")
def update_tier(tier_key):
    err = require_admin()
    if err:
        return err
    
    global PRODUCT_DATA, TIERS
    data = request.get_json() or {}
    
    if tier_key not in PRODUCT_DATA["tiers"]:
        PRODUCT_DATA["tiers"][tier_key] = {}
    
    tier = PRODUCT_DATA["tiers"][tier_key]
    if "name" in data:
        tier["name"] = data["name"]
    if "price" in data:
        tier["price"] = int(data["price"])
    if "description" in data:
        tier["description"] = data["description"]
    
    save_product_data(PRODUCT_DATA)
    TIERS = PRODUCT_DATA["tiers"]
    return jsonify({"status": "updated", "tier": tier})

@app.get("/api/admin/product")
def get_product():
    err = require_admin()
    if err:
        return err
    return jsonify(PRODUCT_DATA)

@app.get("/confirmation")
def confirmation():
    return render_template("confirmation.html", params=request.args)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
