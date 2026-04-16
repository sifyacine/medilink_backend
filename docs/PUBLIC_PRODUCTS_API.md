# Public Products API

**Status:** Active
**Audience:** Public users, patients, partners, and frontend clients
**Purpose:** Read-only product catalog for browsing available MediLink products and contacting the team to place an order.

## Overview

This API is intentionally read-only. It does not provide cart, checkout, or order creation endpoints.
Users can:
- Browse available products
- Search products by text
- Filter by category
- Sort results
- Paginate through the catalog
- Open a product detail page

The public catalog only returns active products.

## Base URL

`/api/products/`

## Endpoints

### List Products

`GET /api/products/`

Returns a paginated list of active products.

### Retrieve Product

`GET /api/products/{id}/`

Returns a detailed public view of a single active product.

## Query Parameters

### Search

`search`

Searches across:
- `name`
- `sku`
- `brand`
- `manufacturer`
- `description`
- `category`

Example:

`GET /api/products/?search=subscription`

### Category Filter

`category`

Supported values:
- `SUBSCRIPTION`
- `SOFTWARE`
- `MEDICAL_SUPPLY`
- `EQUIPMENT`
- `DIGITAL`
- `OTHER`

Example:

`GET /api/products/?category=MEDICAL_SUPPLY`

### Ordering

`ordering`

Supported fields:
- `name`
- `selling_price`
- `rating`
- `stock_quantity`
- `created_at`

Use `-` for descending order.

Examples:
- `GET /api/products/?ordering=name`
- `GET /api/products/?ordering=-created_at`

### Pagination

The endpoint uses page-number pagination.

Parameters:
- `page`: page number
- `page_size`: number of items per page

Defaults:
- `page_size = 20`
- `max page_size = 100`

Examples:
- `GET /api/products/?page=2`
- `GET /api/products/?page_size=12`
- `GET /api/products/?page=3&page_size=50`

## Example Response

```json
{
  "count": 42,
  "next": "http://localhost:8000/api/products/?page=2",
  "previous": null,
  "results": [
    {
      "id": "2f58c6f5-5f53-4a46-8db5-5a9c0c2f0f47",
      "name": "Premium Provider Subscription",
      "sku": "SUB-001",
      "image_url": "http://localhost:8000/media/products/subscription.png",
      "gallery_images": [],
      "description": "Monthly subscription for providers.",
      "brand": "MediLink",
      "manufacturer": "MediLink",
      "category": "SUBSCRIPTION",
      "currency": "DZD",
      "selling_price": "5000.00",
      "discount_type": "PERCENTAGE",
      "discount_value": "10.00",
      "effective_price": "4500.00",
      "stock_quantity": 100,
      "low_stock_threshold": 5,
      "is_low_stock": false,
      "rating": "4.80",
      "rating_count": 120,
      "created_at": "2026-04-16T10:20:00Z"
    }
  ]
}
```

## Public Detail Response

`GET /api/products/{id}/`

Includes the same public fields as the list response, plus:
- `updated_at`

## Notes for Frontends

- Show only active products from this endpoint.
- Use the `search` param for live search bars.
- Use `page_size` for mobile or desktop layout tuning.
- Contact the Medilink team directly from the UI to order products.
- Do not build cart or checkout flows from this API, because none are provided.

## Permissions

- No authentication required
- Read-only access
- Admin product CRUD remains under `/api/admin/products/`

## Related Admin Endpoints

For internal management only:
- `GET /api/admin/products/`
- `POST /api/admin/products/`
- `PATCH /api/admin/products/{id}/toggle/`
