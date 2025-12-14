# Digital Product System

Complete e-commerce platform for selling digital products (Jupyter Book + interactive notebooks) with email-based authentication and Square payment processing.

## Architecture

### Services

- **Caddy** - Reverse proxy with automatic Let's Encrypt TLS
- **Store** - Flask app with Square checkout and admin API for product management
- **Auth/Events API** - OTP email login via Mailgun, JWT sessions, license management
- **Events Worker** - Background job processor for emails and webhooks
- **WWW** - Public landing page
- **Book** - Static Jupyter Book site (gated by auth)
- **Lab** - JupyterLab interactive environment (gated by auth)
- **Voilà** - Interactive notebook dashboards (gated by auth)
- **Redis** - Queue for background jobs
- **PostgreSQL** - License and user data (TODO: not yet deployed)

### Current Status

✅ **Live in Staging/Development**
- Domain: https://scideology.app
- Store with Square **sandbox** checkout (test mode only)
- Admin API for product management
- Public landing page
- Auth API with OTP login

⚠️ **Partially Implemented**
- Square webhook handler (exists but not wired to license provisioning)
- License database (stubbed with Redis, needs PostgreSQL)

❌ **Not Yet Deployed**
- Jupyter Book site (build fails - Node.js issue)
- JupyterLab and Voilà services
- Post-purchase license provisioning
- Automated access email delivery

## Deployment

### Server Setup

**Droplet**: DigitalOcean s-2vcpu-4gb (Ubuntu 22.04)  
**IP**: 64.23.240.144  
**DNS**: All A records point to droplet IP
- scideology.app
- www.scideology.app
- login.scideology.app
- book.scideology.app (not active)
- lab.scideology.app (not active)
- app.scideology.app (not active)

### Deploy Commands

```bash
# SSH into droplet
ssh root@64.23.240.144

# Navigate to repo
cd /root/digital-product-system

# Pull latest
git pull

# Deploy all services
docker compose -f docker-compose.caddy.yml up -d --build

# Deploy specific service
docker compose -f docker-compose.caddy.yml up -d --build store
```

### Environment Variables

All secrets in `/root/digital-product-system/.env`:

```bash
# Database (not yet used)
POSTGRES_USER=scideology
POSTGRES_PASSWORD=***
POSTGRES_DB=scideology

# Redis
REDIS_PASSWORD=***

# Auth & Email
SECRET_KEY=***
MAILGUN_API_KEY=***
MAILGUN_DOMAIN=em.scideology.app
MAILGUN_FROM=Scideology <noreply@em.scideology.app>
MAILGUN_SIGNING_KEY=***
MAILGUN_WEBHOOK_KEY=***

# Square (sandbox)
SQUARE_ACCESS_TOKEN=***
SQUARE_LOCATION_ID=L22KKDYRBBJF7
SQUARE_BASE=https://connect.squareupsandbox.com

# Pricing (cents)
PRICE_INDIVIDUAL=1499
PRICE_ACADEMIC=9999
PRICE_CORPORATE=49999
CURRENCY=USD

# Domains
BASE_DOMAIN=scideology.app
APP_DOMAIN=app.scideology.app
EVENTS_DOMAIN=login.scideology.app
BOOK_DOMAIN=book.scideology.app
LAB_DOMAIN=lab.scideology.app
LETSENCRYPT_EMAIL=admin@scideology.app

# Jupyter
JUPYTER_TOKEN=***

# Store Admin
ADMIN_API_KEY=***
```

## Store Admin API

Manage product content dynamically via REST API.

**Base URL**: https://scideology.app  
**Auth**: Header `X-Admin-Key: <your-key>` or query param `?api_key=<your-key>`

### Endpoints

```bash
# Get product data
GET /api/admin/product

# Update entire product
POST /api/admin/product
{"title": "...", "description": "...", "hero_image": "...", "gallery_images": [...]}

# Update individual fields
POST /api/admin/product/title
{"value": "New Title"}

POST /api/admin/product/description
{"value": "New description"}

POST /api/admin/product/hero_image
{"url": "https://example.com/hero.jpg"}

POST /api/admin/product/gallery_images
{"images": ["url1", "url2"]}

# Update pricing tier (individual/academic/corporate)
POST /api/admin/tiers/<tier_key>
{"name": "...", "price": 1999, "description": "..."}
```

See `store/API.md` for complete documentation.

## Square Sandbox Testing

**Test Card**: 4111 1111 1111 1111  
**Expiry**: Any future date  
**CVV**: Any 3 digits  

Checkout flow redirects to Square sandbox, processes payment, returns to `/confirmation`.

## Development

### Local Setup

```bash
# Install dependencies (each service has its own requirements.txt)
cd store && pip install -r requirements.txt
cd backend && pip install -r requirements.txt

# Run store locally
cd store
FLASK_APP=app.py flask run
```

### CI/CD

GitHub Actions workflow builds and pushes `events-api` image to GHCR on push to main.

## Next Steps

1. **Fix Jupyter Book build** - Add Node.js to builder, resolve config issues
2. **Deploy PostgreSQL** - Replace Redis stubs with proper database
3. **Wire Square webhooks** - Auto-provision licenses on payment completion
4. **Email access credentials** - Send OTP login link post-purchase
5. **Deploy Lab and Voilà** - Protected notebook environments
6. **Production Square** - Switch from sandbox to live credentials
