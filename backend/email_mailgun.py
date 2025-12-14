import os
import requests
from jinja2 import Template

MAILGUN_DOMAIN = os.environ.get("MAILGUN_DOMAIN")
MAILGUN_API_KEY = os.environ.get("MAILGUN_API_KEY")
MAILGUN_FROM = os.environ.get("MAILGUN_FROM", f"Parallel Critiques <no-reply@{MAILGUN_DOMAIN}>")

TEMPLATES = {
    "magic_link": {
        "subject": "Your secure sign-in link",
        "html": Template("""
        <p>Hi {{ first_name or 'there' }},</p>
        <p>Click the secure link below to sign in. This link will expire in {{ minutes }} minutes and can be used once.</p>
        <p><a href="{{ url }}">Sign in now</a></p>
        <p>If you didn't request this, you can ignore it.</p>
        """)
    },
    "otp_code": {
        "subject": "Your verification code",
        "html": Template("""
        <p>Hi {{ first_name or 'there' }},</p>
        <p>Your verification code is:</p>
        <p style="font-size:22px;font-weight:700;letter-spacing:3px">{{ code }}</p>
        <p>This code expires in {{ minutes }} minutes.</p>
        <p>After entering the code, you will be signed in to {{ host or 'the site' }}.</p>
        """)
    },
    "welcome": {
        "subject": "Welcome — Your access details",
        "html": Template("""
        <p>Hi {{ first_name or 'there' }},</p>
        <p>Thanks for your purchase. Use the links below to get started:</p>
        <ul>
          <li><a href="https://{{ book_domain }}">Open the Book</a></li>
          {% if lab_domain %}<li><a href="https://{{ lab_domain }}">Open JupyterLab</a></li>{% endif %}
          {% if app_domain %}<li><a href="https://{{ app_domain }}">Open the App</a></li>{% endif %}
        </ul>
        <p>If you need help, reply to this email.</p>
        <p>— Team</p>
        """)
    },
    "abandoned_cart": {
        "subject": "You left something in your cart",
        "html": Template("""
        <p>Hi {{ first_name or 'there' }},</p>
        <p>You started checking out {{ tier }} but didn’t finish. Pick up where you left off:</p>
        <p><a href="{{ resume_url }}">Resume checkout</a></p>
        <p>Questions? Just reply.</p>
        """)
    }
}


def send_mailgun(template: str, to: str, variables: dict) -> requests.Response:
    assert MAILGUN_DOMAIN and MAILGUN_API_KEY, "Mailgun not configured"
    tmpl = TEMPLATES[template]
    subject = tmpl["subject"]
    html = tmpl["html"].render(**variables)
    return requests.post(
        f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
        auth=("api", MAILGUN_API_KEY),
        data={
            "from": MAILGUN_FROM,
            "to": [to],
            "subject": subject,
            "html": html,
            "o:tag": [template],
        },
        timeout=10,
    )
