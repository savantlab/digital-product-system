# Terms of Use API Documentation

## Overview
API for managing Terms of Use (TOU) content with versioning, activation control, and user acceptance tracking.

## Database Setup
Run the migration first:
```bash
psql $DB_URL < migrations/001_add_tou_content.sql
```

This creates:
- `tou_content` table: Stores TOU versions with JSONB content
- `tou_acceptances` table: Tracks user acceptances with timestamps
- Default version 1 with initial TOU content

## API Endpoints

### 1. Get Active TOU
**GET** `/api/tou`

Returns the currently active Terms of Use.

**Response:**
```json
{
  "ok": true,
  "data": {
    "version": 1,
    "content": {
      "sections": [
        {
          "title": "1. Acceptance of Terms",
          "content": "By accessing this course..."
        },
        ...
      ],
      "agreement_text": "I am at least 18 years old..."
    },
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

### 2. Get Specific TOU Version
**GET** `/api/tou/version/<version>`

Returns a specific version of the TOU.

**Response:**
```json
{
  "ok": true,
  "data": {
    "version": 1,
    "content": { ... },
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
    "created_by": "admin@example.com"
  }
}
```

### 3. Create New TOU Version
**POST** `/api/tou`

Creates a new version of the Terms of Use.

**Request Body:**
```json
{
  "content": {
    "sections": [
      {
        "title": "1. Acceptance of Terms",
        "content": "Terms content here..."
      },
      {
        "title": "2. Another Section",
        "content": "More content...\n• Bullet point 1\n• Bullet point 2"
      }
    ],
    "agreement_text": "I agree to these terms..."
  },
  "created_by": "admin@example.com",
  "set_active": false
}
```

**Parameters:**
- `content` (required): JSONB object with `sections` array and `agreement_text`
- `created_by` (optional): Email of admin creating the version
- `set_active` (optional): If true, immediately activates this version (deactivates all others)

**Response:**
```json
{
  "ok": true,
  "data": {
    "id": 2,
    "version": 2,
    "is_active": false,
    "created_at": "2024-01-02T00:00:00Z"
  }
}
```

### 4. Update TOU Version
**PUT** `/api/tou/version/<version>`

Updates an existing TOU version's content or activation status.

**Request Body:**
```json
{
  "content": {
    "sections": [...],
    "agreement_text": "..."
  },
  "set_active": true,
  "updated_by": "admin@example.com"
}
```

**Parameters:**
- `content` (optional): New content to replace existing
- `set_active` (optional): Activate/deactivate this version
- `updated_by` (optional): Email of admin updating the version

**Response:**
```json
{
  "ok": true,
  "data": {
    "version": 1,
    "is_active": true,
    "updated_at": "2024-01-02T12:00:00Z"
  }
}
```

### 5. Record TOU Acceptance
**POST** `/api/tou/accept`

Records a user's acceptance of the TOU.

**Request Body:**
```json
{
  "email": "user@example.com",
  "version": 1
}
```

**Response:**
```json
{
  "ok": true,
  "data": {
    "id": 123,
    "accepted_at": "2024-01-02T12:34:56Z"
  }
}
```

**Note:** IP address and user agent are automatically captured from request headers.

### 6. Get TOU History
**GET** `/api/tou/history`

Returns all TOU versions ordered by version number (newest first).

**Response:**
```json
{
  "ok": true,
  "data": [
    {
      "version": 2,
      "is_active": false,
      "created_at": "2024-01-02T00:00:00Z",
      "updated_at": "2024-01-02T00:00:00Z",
      "created_by": "admin@example.com"
    },
    {
      "version": 1,
      "is_active": true,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z",
      "created_by": "system"
    }
  ]
}
```

## Content Format

The `content` JSONB field has this structure:

```json
{
  "sections": [
    {
      "title": "Section Title",
      "content": "Section content.\n• Bullet 1\n• Bullet 2"
    }
  ],
  "agreement_text": "Agreement checkbox text"
}
```

**Formatting in content:**
- Use `\n` for line breaks
- Use `•` at the start of lines for bullet points
- The frontend automatically renders these as `<ul>` lists
- Use `<strong>...</strong>` for bold text (rendered in frontend)
- Email links are auto-detected if formatted as: "contact: email@example.com"

## Version Management

- Only one version can be active at a time
- Setting `set_active: true` automatically deactivates all other versions
- Version numbers auto-increment (1, 2, 3, ...)
- Cannot delete versions (audit trail requirement)
- Can update content or activation status of any version

## Security Notes

- Add authentication middleware for POST/PUT endpoints (admin only)
- Consider rate limiting on acceptance endpoint
- IP and user agent are logged for acceptance audit trail
- CORS configured via `ALLOWED_ORIGINS` environment variable

## Usage Example

```bash
# Create a new TOU version
curl -X POST http://localhost:8001/api/tou \
  -H "Content-Type: application/json" \
  -d '{
    "content": {
      "sections": [
        {"title": "1. Terms", "content": "Updated terms..."}
      ],
      "agreement_text": "I agree"
    },
    "created_by": "admin@example.com",
    "set_active": true
  }'

# Get active TOU
curl http://localhost:8001/api/tou

# Update version 2 to make it active
curl -X PUT http://localhost:8001/api/tou/version/2 \
  -H "Content-Type: application/json" \
  -d '{"set_active": true, "updated_by": "admin@example.com"}'

# Record user acceptance
curl -X POST http://localhost:8001/api/tou/accept \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "version": 1}'
```

## Frontend Integration

The React component automatically fetches from `/api/tou` and renders:
- All sections with proper formatting
- Bullet lists as `<ul>` elements
- Email links as clickable `<a>` tags
- Agreement checkbox with dynamic text
- Loading and error states

Set environment variable in `.env`:
```
VITE_API_BASE=http://localhost:8001
```
