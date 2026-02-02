# Provider Dashboards - Social Media API

## Overview

This documentation covers the **Social Media API** for Provider Web Dashboards. Providers can add their social media links (Facebook, Instagram, LinkedIn, YouTube, TikTok, Twitter, or custom platforms) to their profile, which can be displayed to patients.

---

## Table of Contents

1. [Base URL](#base-url)
2. [Authentication](#authentication)
3. [Supported Platforms](#supported-platforms)
4. [Endpoints](#endpoints)
   - [List Social Links](#list-social-links)
   - [Create Social Link](#create-social-link)
   - [Get Social Link Details](#get-social-link-details)
   - [Update Social Link](#update-social-link)
   - [Delete Social Link](#delete-social-link)
5. [Error Handling](#error-handling)
6. [Integration Examples](#integration-examples)

---

## Base URL

```
https://dzmedilink.duckdns.org/api/
```

---

## Authentication

All endpoints require authentication. Include your token in every request:

```
Authorization: Token <your_token_here>
```

---

## Supported Platforms

| Platform Code | Display Name | Notes |
|---------------|--------------|-------|
| `FACEBOOK` | Facebook | |
| `INSTAGRAM` | Instagram | |
| `TWITTER` | Twitter / X | |
| `LINKEDIN` | LinkedIn | |
| `YOUTUBE` | YouTube | |
| `TIKTOK` | TikTok | |
| `OTHER` | Other | Requires `custom_label` |

---

## Endpoints

### List Social Links

Get all social media links for the authenticated provider.

```
GET /api/social-links/
```

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `platform` | string | Filter by platform code |
| `is_visible` | boolean | Filter by visibility status |
| `ordering` | string | Order by: `display_order`, `platform` |

#### Response (200 OK)

```json
[
    {
        "id": 1,
        "platform": "FACEBOOK",
        "platform_display": "Facebook",
        "url": "https://facebook.com/dr.kaddour.clinic",
        "custom_label": null,
        "is_visible": true,
        "display_order": 0,
        "created_at": "2026-01-15T10:30:00Z",
        "updated_at": "2026-01-15T10:30:00Z"
    },
    {
        "id": 2,
        "platform": "INSTAGRAM",
        "platform_display": "Instagram",
        "url": "https://instagram.com/dr.kaddour",
        "custom_label": null,
        "is_visible": true,
        "display_order": 1,
        "created_at": "2026-01-15T10:35:00Z",
        "updated_at": "2026-01-15T10:35:00Z"
    },
    {
        "id": 3,
        "platform": "OTHER",
        "platform_display": "Other",
        "url": "https://doctolib.dz/dr-kaddour",
        "custom_label": "Doctolib Profile",
        "is_visible": true,
        "display_order": 2,
        "created_at": "2026-01-15T11:00:00Z",
        "updated_at": "2026-01-15T11:00:00Z"
    }
]
```

---

### Create Social Link

Add a new social media link to your provider profile.

```
POST /api/social-links/
```

#### Request Body

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `platform` | ✅ Yes | string | Platform code (see [Supported Platforms](#supported-platforms)) |
| `url` | ✅ Yes | string | Full URL to your social profile |
| `custom_label` | ⚠️ Conditional | string | **Required** if `platform` is `OTHER` |
| `is_visible` | ❌ No | boolean | Show publicly (default: `true`) |
| `display_order` | ❌ No | integer | Display order (default: `0`) |

#### Example: Standard Platform

```json
{
    "platform": "INSTAGRAM",
    "url": "https://instagram.com/dr.kaddour",
    "is_visible": true,
    "display_order": 0
}
```

#### Example: Custom Platform (OTHER)

```json
{
    "platform": "OTHER",
    "url": "https://doctolib.dz/dr-kaddour",
    "custom_label": "Doctolib Profile",
    "is_visible": true,
    "display_order": 5
}
```

#### Response (201 Created)

```json
{
    "id": 4,
    "platform": "INSTAGRAM",
    "platform_display": "Instagram",
    "url": "https://instagram.com/dr.kaddour",
    "custom_label": null,
    "is_visible": true,
    "display_order": 0,
    "created_at": "2026-02-02T14:30:00Z",
    "updated_at": "2026-02-02T14:30:00Z"
}
```

---

### Get Social Link Details

Get details of a specific social media link.

```
GET /api/social-links/{id}/
```

#### Response (200 OK)

```json
{
    "id": 1,
    "platform": "FACEBOOK",
    "platform_display": "Facebook",
    "url": "https://facebook.com/dr.kaddour.clinic",
    "custom_label": null,
    "is_visible": true,
    "display_order": 0,
    "created_at": "2026-01-15T10:30:00Z",
    "updated_at": "2026-01-15T10:30:00Z"
}
```

---

### Update Social Link

Update an existing social media link.

```
PUT /api/social-links/{id}/
```

or for partial updates:

```
PATCH /api/social-links/{id}/
```

#### Request Body

```json
{
    "url": "https://facebook.com/dr.kaddour.official",
    "is_visible": true
}
```

#### Response (200 OK)

```json
{
    "id": 1,
    "platform": "FACEBOOK",
    "platform_display": "Facebook",
    "url": "https://facebook.com/dr.kaddour.official",
    "custom_label": null,
    "is_visible": true,
    "display_order": 0,
    "created_at": "2026-01-15T10:30:00Z",
    "updated_at": "2026-02-02T15:00:00Z"
}
```

---

### Delete Social Link

Remove a social media link.

```
DELETE /api/social-links/{id}/
```

#### Response (204 No Content)

No content is returned on successful deletion.

---

## Error Handling

### Validation Errors

#### Missing Custom Label for OTHER Platform

```json
{
    "non_field_errors": ["custom_label is required when platform is OTHER."]
}
```

#### Invalid URL Format

```json
{
    "url": ["Enter a valid URL."]
}
```

#### Invalid Platform Code

```json
{
    "platform": ["\"INVALID\" is not a valid choice."]
}
```

### Permission Errors

```json
{
    "detail": "You do not have permission to perform this action."
}
```

### Not Found

```json
{
    "detail": "Not found."
}
```

---

## Integration Examples

### JavaScript - Add Social Media Links

```javascript
// Add Instagram link
async function addSocialLink() {
    const response = await fetch('https://dzmedilink.duckdns.org/api/social-links/', {
        method: 'POST',
        headers: {
            'Authorization': `Token ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            platform: 'INSTAGRAM',
            url: 'https://instagram.com/my-clinic',
            is_visible: true,
            display_order: 0
        })
    });
    
    return await response.json();
}
```

### JavaScript - Display Social Links on Profile

```javascript
// Fetch and display social links
async function loadSocialLinks() {
    const response = await fetch('https://dzmedilink.duckdns.org/api/social-links/', {
        headers: {
            'Authorization': `Token ${token}`
        }
    });
    
    const links = await response.json();
    
    const container = document.getElementById('social-links');
    container.innerHTML = links
        .filter(link => link.is_visible)
        .map(link => `
            <a href="${link.url}" target="_blank" class="social-link">
                <i class="fab fa-${link.platform.toLowerCase()}"></i>
                ${link.custom_label || link.platform_display}
            </a>
        `).join('');
}
```

### React Component Example

```jsx
import React, { useState, useEffect } from 'react';

const SocialMediaManager = () => {
    const [links, setLinks] = useState([]);
    const [newLink, setNewLink] = useState({
        platform: 'FACEBOOK',
        url: '',
        custom_label: '',
        is_visible: true,
        display_order: 0
    });
    
    const platforms = [
        { value: 'FACEBOOK', label: 'Facebook' },
        { value: 'INSTAGRAM', label: 'Instagram' },
        { value: 'TWITTER', label: 'Twitter' },
        { value: 'LINKEDIN', label: 'LinkedIn' },
        { value: 'YOUTUBE', label: 'YouTube' },
        { value: 'TIKTOK', label: 'TikTok' },
        { value: 'OTHER', label: 'Other' }
    ];
    
    useEffect(() => {
        fetchLinks();
    }, []);
    
    const fetchLinks = async () => {
        const response = await api.get('/social-links/');
        setLinks(response.data);
    };
    
    const handleAdd = async () => {
        await api.post('/social-links/', newLink);
        fetchLinks();
        setNewLink({ platform: 'FACEBOOK', url: '', custom_label: '', is_visible: true, display_order: 0 });
    };
    
    const handleDelete = async (id) => {
        await api.delete(`/social-links/${id}/`);
        fetchLinks();
    };
    
    return (
        <div className="social-media-manager">
            <h3>Your Social Media Links</h3>
            
            {/* Existing links */}
            <ul>
                {links.map(link => (
                    <li key={link.id}>
                        <a href={link.url}>{link.platform_display}</a>
                        <button onClick={() => handleDelete(link.id)}>Delete</button>
                    </li>
                ))}
            </ul>
            
            {/* Add new link form */}
            <div className="add-link-form">
                <select
                    value={newLink.platform}
                    onChange={e => setNewLink({...newLink, platform: e.target.value})}
                >
                    {platforms.map(p => (
                        <option key={p.value} value={p.value}>{p.label}</option>
                    ))}
                </select>
                
                <input
                    type="url"
                    placeholder="Social media URL"
                    value={newLink.url}
                    onChange={e => setNewLink({...newLink, url: e.target.value})}
                />
                
                {newLink.platform === 'OTHER' && (
                    <input
                        type="text"
                        placeholder="Custom label (required)"
                        value={newLink.custom_label}
                        onChange={e => setNewLink({...newLink, custom_label: e.target.value})}
                    />
                )}
                
                <button onClick={handleAdd}>Add Link</button>
            </div>
        </div>
    );
};

export default SocialMediaManager;
```

---

## Notes

### Automatic Provider Association

When you create a social media link as a provider, it is automatically attached to your provider profile. You don't need to manually specify `content_type` or `object_id` - the system handles this for you.

### Display Order

Use `display_order` to control how links appear when displayed to patients. Lower numbers appear first.

### Visibility Control

Set `is_visible` to `false` if you want to temporarily hide a social link without deleting it.

### Multiple Links Per Platform

You can add multiple links for the same platform if needed (e.g., multiple YouTube channels).
