import os
import uuid
from flask import Flask, render_template, request, redirect, url_for
import requests

app = Flask(__name__)

# Pricing (in cents)
PRICE_INDIVIDUAL = int(os.environ.get("PRICE_INDIVIDUAL", "1499"))
PRICE_ACADEMIC   = int(os.environ.get("PRICE_ACADEMIC",   "9999"))
PRICE_CORPORATE  = int(os.environ.get("PRICE_CORPORATE",  "49999"))
CURRENCY = os.environ.get("CURRENCY", "USD")

# Square
SQUARE_ACCESS_TOKEN = os.environ.get("SQUARE_ACCESS_TOKEN")
SQUARE_LOCATION_ID  = os.environ.get("SQUARE_LOCATION_ID")
SQUARE_BASE         = os.environ.get("SQUARE_BASE", "https://connect.squareup.com")

STORE_BASE_URL      = os.environ.get("STORE_BASE_URL", "https://scideology.app")

TIERS = {
    "individual": {"name": "Individual", "price": PRICE_INDIVIDUAL},
    "academic":   {"name": "Academic/Educational", "price": PRICE_ACADEMIC},
    "corporate":  {"name": "Corporate/Agency", "price": PRICE_CORPORATE},
}

@app.get("/")
def product():
    return render_template("product.html", tiers=TIERS)

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
                    "name": f"Parallel Critiques — {tier[name]} License",
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

@app.get("/confirmation")
def confirmation():
    return render_template("confirmation.html", params=request.args)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
