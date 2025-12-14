# Deployment Notes - PRIVATE

**DO NOT COMMIT THIS FILE TO GIT**

## Square Production Credentials

**Application ID**: `sq0idp-rcYfDyLkAhy642fZ8jpHUA`  
**Access Token**: `EAAAl_Wfh_A_K9n1GlAtePkhjc9i-OkxN5qzE2SLrOeUtlRaXwwckjhW-MZu_1z6`  
**Location ID**: `LVYCTH4YP5KJ7`

## Current Status

- **Staging**: Using Square sandbox credentials
- **Ready to deploy**: Two-column product page, admin API, hero image
- **Pending**: License provisioning, email delivery, PostgreSQL

## Switch to Production Square

When ready to accept real payments:

```bash
# 1. SSH into droplet
ssh root@64.23.240.144

# 2. Edit environment file
nano /root/digital-product-system/.env

# 3. Update these lines:
SQUARE_ACCESS_TOKEN=EAAAl_Wfh_A_K9n1GlAtePkhjc9i-OkxN5qzE2SLrOeUtlRaXwwckjhW-MZu_1z6
SQUARE_LOCATION_ID=LVYCTH4YP5KJ7
SQUARE_BASE=https://connect.squareup.com

# 4. Restart store service
cd /root/digital-product-system
docker compose -f docker-compose.caddy.yml restart store
```

## Before Going Live Checklist

- [ ] Complete license provisioning system (PostgreSQL)
- [ ] Wire Square webhook to create licenses on payment
- [ ] Set up automated email delivery with access instructions
- [ ] Test full purchase-to-access flow in sandbox
- [ ] Deploy Jupyter Book, Lab, and Voilà services
- [ ] Verify auth/OTP login works for purchased users
- [ ] Update admin API key to production-strength value
- [ ] Test webhook security (Square signature verification)
- [ ] Set up monitoring/alerting for payment failures
- [ ] Document customer support procedures

## Production Environment

**Droplet**: DigitalOcean s-2vcpu-4gb, Ubuntu 22.04  
**IP**: 64.23.240.144  
**Domains**:
- scideology.app (store)
- www.scideology.app (landing)
- login.scideology.app (auth)
- book.scideology.app (not active)
- lab.scideology.app (not active)
- app.scideology.app (not active)

**Admin API Key**: `scideology_admin_2024_secure_key` (change before production!)

## Deployment Commands

```bash
# Pull latest from deploy branch
cd /root/digital-product-system
git pull

# Rebuild and restart all services
docker compose -f docker-compose.caddy.yml up -d --build

# Restart specific service
docker compose -f docker-compose.caddy.yml restart store

# View logs
docker compose -f docker-compose.caddy.yml logs -f store
```

## Rollback Procedure

```bash
# Revert to previous commit
cd /root/digital-product-system
git log --oneline  # Find commit hash
git reset --hard <commit-hash>
docker compose -f docker-compose.caddy.yml up -d --build
```

---

**Last Updated**: 2025-12-14  
**Status**: Sandbox/Staging
