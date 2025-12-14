# Store Admin API

All admin endpoints require authentication via `X-Admin-Key` header or `?api_key=` query parameter.

## Get Product Data

```bash
GET /api/admin/product
X-Admin-Key: your-admin-key
```

Returns complete product configuration.

## Update Entire Product

```bash
POST /api/admin/product
X-Admin-Key: your-admin-key
Content-Type: application/json

{
  "title": "New Product Title",
  "description": "Updated description",
  "hero_image": "https://example.com/hero.jpg",
  "gallery_images": ["https://example.com/img1.jpg", "https://example.com/img2.jpg"]
}
```

## Update Individual Fields

### Title
```bash
POST /api/admin/product/title
X-Admin-Key: your-admin-key
Content-Type: application/json

{"value": "New Title"}
```

### Description
```bash
POST /api/admin/product/description
X-Admin-Key: your-admin-key
Content-Type: application/json

{"value": "New product description"}
```

### Hero Image
```bash
POST /api/admin/product/hero_image
X-Admin-Key: your-admin-key
Content-Type: application/json

{"url": "https://example.com/hero.jpg"}
```

### Gallery Images
```bash
POST /api/admin/product/gallery_images
X-Admin-Key: your-admin-key
Content-Type: application/json

{"images": ["https://example.com/1.jpg", "https://example.com/2.jpg"]}
```

## Update Pricing Tier

```bash
POST /api/admin/tiers/individual
X-Admin-Key: your-admin-key
Content-Type: application/json

{
  "name": "Individual License",
  "price": 2999,
  "description": "Perfect for personal use"
}
```

Price is in cents (2999 = $29.99).

Available tiers: `individual`, `academic`, `corporate` (or create new ones).

## Example Usage

```bash
# Update title
curl -X POST https://scideology.app/api/admin/product/title \
  -H "X-Admin-Key: your-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"value": "Text Analysis Masterclass"}'

# Update individual tier pricing
curl -X POST https://scideology.app/api/admin/tiers/individual \
  -H "X-Admin-Key: your-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"name": "Personal", "price": 1999, "description": "Single user license"}'

# Get current product data
curl https://scideology.app/api/admin/product?api_key=your-secret-key
```
