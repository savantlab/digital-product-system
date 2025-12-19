# Email API Documentation

The Email API provides endpoints for sending, tracking, and managing emails with user persistence.

## Base URL
All endpoints are prefixed with `/api/email`

## Authentication
Most endpoints require admin authentication (not yet implemented). User-facing endpoints are marked below.

---

## Endpoints

### 1. Send Email (Single or Batch)
Send an email to one or multiple recipients and track in the database.

**Endpoint:** `POST /api/email/send`

**Request Body (Single):**
```json
{
  "to": "user@example.com",
  "template": "welcome",
  "variables": {
    "first_name": "John",
    "code": "123456",
    "minutes": 10
  },
  "auth_code": "abc123",
  "metadata": {
    "license_id": 123,
    "tier": "individual"
  }
}
```

**Request Body (Batch):**
```json
{
  "to": ["user1@example.com", "user2@example.com", "user3@example.com"],
  "template": "welcome",
  "variables": {
    "first_name": "Team Member"
  },
  "metadata": {
    "batch_id": "team-onboarding-2024"
  }
}
```

**Parameters:**
- `to` (required): Recipient email address (string) OR array of email addresses
- `template` (required): Template name (`otp_code`, `magic_link`, `welcome`, `abandoned_cart`)
- `variables` (required): Template variables object
- `auth_code` (optional): OTP or auth code for tracking with authentication flow
- `metadata` (optional): Additional tracking data (JSON object)

**Response (Single):**
```json
{
  "ok": true,
  "email_log_id": 123,
  "status": "sent",
  "mailgun_id": "20240101.12345@mg.example.com"
}
```

**Response (Batch):**
```json
{
  "ok": true,
  "batch": true,
  "sent": 3,
  "failed": 0,
  "results": [
    {
      "email": "user1@example.com",
      "email_log_id": 123,
      "status": "sent",
      "mailgun_id": "20240101.12345@mg.example.com",
      "error": null
    },
    {
      "email": "user2@example.com",
      "email_log_id": 124,
      "status": "sent",
      "mailgun_id": "20240101.12346@mg.example.com",
      "error": null
    },
    {
      "email": "user3@example.com",
      "email_log_id": 125,
      "status": "sent",
      "mailgun_id": "20240101.12347@mg.example.com",
      "error": null
    }
  ]
}
```

---

### 2. Get Email Status
Get the delivery status of a sent email.

**Endpoint:** `GET /api/email/status/{email_log_id}`

**Response:**
```json
{
  "ok": true,
  "email_log": {
    "id": 123,
    "email": "user@example.com",
    "template": "otp_code",
    "auth_code": "123456",
    "status": "delivered",
    "sent_at": "2024-01-01T12:00:00Z",
    "delivered_at": "2024-01-01T12:00:05Z",
    "opened_at": "2024-01-01T12:05:00Z",
    "clicked_at": null,
    "failed_at": null
  }
}
```

---

### 3. Get Email History
Get email history for a user by email address.

**Endpoint:** `GET /api/email/history/{email}?limit=50`

**Parameters:**
- `limit` (optional): Maximum number of emails to return (default: 50, max: 200)

**Response:**
```json
{
  "ok": true,
  "emails": [
    {
      "id": 123,
      "template": "otp_code",
      "auth_code": "123456",
      "status": "delivered",
      "sent_at": "2024-01-01T12:00:00Z",
      "delivered_at": "2024-01-01T12:00:05Z"
    }
  ]
}
```

---

### 4. Get User Information
Get user information by email address (licenses + recent auth activity).

**Endpoint:** `GET /api/email/user/{email}`

**Response:**
```json
{
  "ok": true,
  "user": {
    "email": "user@example.com",
    "licenses": [
      {
        "id": 1,
        "tier": "individual",
        "owner_email": "user@example.com",
        "is_active": true,
        "expires": null,
        "created_at": "2024-01-01T12:00:00Z"
      }
    ],
    "recent_auth": [
      {
        "template": "otp_code",
        "auth_code": "123456",
        "sent_at": "2024-01-01T12:00:00Z"
      }
    ]
  }
}
```

---

### 5. Trigger Welcome Email
Trigger welcome email after purchase.

**Endpoint:** `POST /api/email/trigger/welcome`

**Request Body:**
```json
{
  "email": "user@example.com",
  "first_name": "John",
  "license_id": 123
}
```

**Response:**
```json
{
  "ok": true
}
```

---

### 6. Trigger Abandoned Cart Email
Trigger abandoned cart reminder email.

**Endpoint:** `POST /api/email/trigger/abandoned-cart`

**Request Body:**
```json
{
  "email": "user@example.com",
  "first_name": "John",
  "tier": "individual",
  "cart_id": "abc123"
}
```

**Response:**
```json
{
  "ok": true
}
```

---

## Email Templates

### Available Templates

1. **otp_code** - Two-factor authentication code
   - Variables: `first_name`, `code`, `minutes`, `host`

2. **magic_link** - Passwordless login link
   - Variables: `first_name`, `url`, `minutes`

3. **welcome** - Post-purchase welcome email
   - Variables: `first_name`, `book_domain`, `lab_domain`, `app_domain`

4. **abandoned_cart** - Cart abandonment reminder
   - Variables: `first_name`, `tier`, `resume_url`

---

## User Tracking

### Authentication Flow Tracking

When a user logs in:
1. OTP email is sent via `/api/auth/start`
2. Email is logged to `email_logs` table with `auth_code` field
3. User's email and auth code persist in database
4. Can query user's auth history via `/api/email/user/{email}`

### Database Schema

**email_logs table:**
```sql
CREATE TABLE email_logs (
    id SERIAL PRIMARY KEY,
    email TEXT NOT NULL,
    template TEXT NOT NULL,
    auth_code TEXT,  -- Links to OTP/auth flow
    mailgun_id TEXT,
    status TEXT NOT NULL DEFAULT 'sent',
    variables JSONB,
    metadata JSONB,
    
    -- Event timestamps (updated by webhooks)
    sent_at TIMESTAMP,
    delivered_at TIMESTAMP,
    opened_at TIMESTAMP,
    clicked_at TIMESTAMP,
    failed_at TIMESTAMP,
    bounced_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Mailgun Webhook Integration

Mailgun webhooks update email status in real-time:
- `delivered` → Updates `delivered_at`
- `opened` → Updates `opened_at`
- `clicked` → Updates `clicked_at`
- `failed` → Updates `failed_at`, `status = 'failed'`
- `bounced` → Updates `bounced_at`, `status = 'bounced'`

Webhook endpoint: `POST /api/email/mailgun/webhook` (already implemented in app.py)

---

## Usage Examples

### Send OTP Email with Tracking
```python
# In auth flow (already integrated in app.py)
code = issue_otp(email="user@example.com", ttl_min=10)

# Email is automatically logged with auth_code for tracking
response = send_mailgun("otp_code", to=email, variables={
    "first_name": "John",
    "code": code,
    "minutes": 10,
    "host": "book.example.com"
})
```

### Send Batch Emails (Team Onboarding)
```python
import requests

# Send welcome emails to entire team
team_emails = ["alice@company.com", "bob@company.com", "charlie@company.com"]

response = requests.post('http://localhost:8001/api/email/send', json={
    "to": team_emails,
    "template": "welcome",
    "variables": {
        "first_name": "Team Member",
        "book_domain": "book.example.com",
        "lab_domain": "lab.example.com",
        "app_domain": "app.example.com"
    },
    "metadata": {
        "batch_id": "team-onboarding-2024-01",
        "license_id": 123
    }
})

result = response.json()
print(f"Sent: {result['sent']}, Failed: {result['failed']}")
```

### Trigger Welcome Email After Purchase
```python
import requests

requests.post('http://localhost:8001/api/email/trigger/welcome', json={
    "email": "user@example.com",
    "first_name": "John",
    "license_id": 123
})
```

### Check User's Email History
```python
import requests

response = requests.get('http://localhost:8001/api/email/history/user@example.com?limit=10')
emails = response.json()['emails']
```

### Get User Info (Licenses + Auth Activity)
```python
import requests

response = requests.get('http://localhost:8001/api/email/user/user@example.com')
user_data = response.json()['user']
print(f"Licenses: {user_data['licenses']}")
print(f"Recent auth: {user_data['recent_auth']}")
```

---

## Environment Variables

Required for email functionality:
```bash
MAILGUN_DOMAIN=mg.example.com
MAILGUN_API_KEY=key-xxxxx
MAILGUN_FROM=Product <no-reply@example.com>
MAILGUN_SIGNING_KEY=xxxxx  # For webhook verification

BOOK_DOMAIN=book.example.com
LAB_DOMAIN=lab.example.com
APP_DOMAIN=app.example.com
EVENTS_DOMAIN=events.example.com

DB_URL=postgresql://user:pass@localhost/dbname
```

---

## Migration

Run the email_logs migration:
```bash
psql $DB_URL < backend/migrations/003_add_email_logs.sql
```
