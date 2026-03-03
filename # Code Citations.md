# Code Citations

## License: unknown
https://github.com/zokeya/gravity_jobcard/blob/36f211385dd63c680e1462c2934ea5c5ae8d299c/.ebextensions/02_nginx.config

```
Here's the **production deployment checklist** for your WebSocket + notification updates:

---

## Production Deployment Guide

### 1. Update `requirements.txt`
Add Daphne (it's installed locally but missing from requirements):
```
daphne>=4.0,<5.0
```
`channels` and `channels-redis` are already listed.

### 2. Install & start Redis
Your production server (`dzmedilink.duckdns.org`) needs Redis for the channel layer. On your DigitalOcean server:
```bash
sudo apt install redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

### 3. Update production settings

In your production `.env` file on the server, add:
```
REDIS_URL=redis://localhost:6379
```

Then update [core/settings/production.py](core/settings/production.py) — add the Redis channel layer override and CORS for WebSocket origins:

```python
# At the end of production.py, add:

# Use Redis channel layer in production (overrides InMemoryChannelLayer from base.py)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [env("REDIS_URL", default="redis://localhost:6379")],
        },
    },
}
```

### 4. Switch from Gunicorn (WSGI) to Daphne (ASGI)
Your server currently runs WSGI, which **doesn't support WebSockets**. Replace it:

**Before** (likely your current systemd service or process):
```bash
gunicorn core.wsgi:application --bind 0.0.0.0:8000
```

**After:**
```bash
daphne -b 0.0.0.0 -p 8000 core.asgi:application
```

If you use a systemd service file (e.g. `/etc/systemd/system/medilink.service`), update the `ExecStart`:
```ini
[Service]
ExecStart=/path/to/venv/bin/daphne -b 0.0.0.0 -p 8000 core.asgi:application
Environment="DJANGO_SETTINGS_MODULE=core.settings.production"
```

### 5. Configure Nginx for WebSocket proxy
Add WebSocket upgrade headers to your Nginx config for `dzmedilink.duckdns.org`:

```nginx
server {
    server_name dzmedilink.duckdns.org;

    # ... existing SSL config ...

    # Regular HTTP traffic (REST API)
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket traffic
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read
```


## License: unknown
https://github.com/zokeya/gravity_jobcard/blob/36f211385dd63c680e1462c2934ea5c5ae8d299c/.ebextensions/02_nginx.config

```
Here's the **production deployment checklist** for your WebSocket + notification updates:

---

## Production Deployment Guide

### 1. Update `requirements.txt`
Add Daphne (it's installed locally but missing from requirements):
```
daphne>=4.0,<5.0
```
`channels` and `channels-redis` are already listed.

### 2. Install & start Redis
Your production server (`dzmedilink.duckdns.org`) needs Redis for the channel layer. On your DigitalOcean server:
```bash
sudo apt install redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

### 3. Update production settings

In your production `.env` file on the server, add:
```
REDIS_URL=redis://localhost:6379
```

Then update [core/settings/production.py](core/settings/production.py) — add the Redis channel layer override and CORS for WebSocket origins:

```python
# At the end of production.py, add:

# Use Redis channel layer in production (overrides InMemoryChannelLayer from base.py)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [env("REDIS_URL", default="redis://localhost:6379")],
        },
    },
}
```

### 4. Switch from Gunicorn (WSGI) to Daphne (ASGI)
Your server currently runs WSGI, which **doesn't support WebSockets**. Replace it:

**Before** (likely your current systemd service or process):
```bash
gunicorn core.wsgi:application --bind 0.0.0.0:8000
```

**After:**
```bash
daphne -b 0.0.0.0 -p 8000 core.asgi:application
```

If you use a systemd service file (e.g. `/etc/systemd/system/medilink.service`), update the `ExecStart`:
```ini
[Service]
ExecStart=/path/to/venv/bin/daphne -b 0.0.0.0 -p 8000 core.asgi:application
Environment="DJANGO_SETTINGS_MODULE=core.settings.production"
```

### 5. Configure Nginx for WebSocket proxy
Add WebSocket upgrade headers to your Nginx config for `dzmedilink.duckdns.org`:

```nginx
server {
    server_name dzmedilink.duckdns.org;

    # ... existing SSL config ...

    # Regular HTTP traffic (REST API)
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket traffic
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read
```


## License: unknown
https://github.com/zokeya/gravity_jobcard/blob/36f211385dd63c680e1462c2934ea5c5ae8d299c/.ebextensions/02_nginx.config

```
Here's the **production deployment checklist** for your WebSocket + notification updates:

---

## Production Deployment Guide

### 1. Update `requirements.txt`
Add Daphne (it's installed locally but missing from requirements):
```
daphne>=4.0,<5.0
```
`channels` and `channels-redis` are already listed.

### 2. Install & start Redis
Your production server (`dzmedilink.duckdns.org`) needs Redis for the channel layer. On your DigitalOcean server:
```bash
sudo apt install redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

### 3. Update production settings

In your production `.env` file on the server, add:
```
REDIS_URL=redis://localhost:6379
```

Then update [core/settings/production.py](core/settings/production.py) — add the Redis channel layer override and CORS for WebSocket origins:

```python
# At the end of production.py, add:

# Use Redis channel layer in production (overrides InMemoryChannelLayer from base.py)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [env("REDIS_URL", default="redis://localhost:6379")],
        },
    },
}
```

### 4. Switch from Gunicorn (WSGI) to Daphne (ASGI)
Your server currently runs WSGI, which **doesn't support WebSockets**. Replace it:

**Before** (likely your current systemd service or process):
```bash
gunicorn core.wsgi:application --bind 0.0.0.0:8000
```

**After:**
```bash
daphne -b 0.0.0.0 -p 8000 core.asgi:application
```

If you use a systemd service file (e.g. `/etc/systemd/system/medilink.service`), update the `ExecStart`:
```ini
[Service]
ExecStart=/path/to/venv/bin/daphne -b 0.0.0.0 -p 8000 core.asgi:application
Environment="DJANGO_SETTINGS_MODULE=core.settings.production"
```

### 5. Configure Nginx for WebSocket proxy
Add WebSocket upgrade headers to your Nginx config for `dzmedilink.duckdns.org`:

```nginx
server {
    server_name dzmedilink.duckdns.org;

    # ... existing SSL config ...

    # Regular HTTP traffic (REST API)
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket traffic
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read
```


## License: unknown
https://github.com/zokeya/gravity_jobcard/blob/36f211385dd63c680e1462c2934ea5c5ae8d299c/.ebextensions/02_nginx.config

```
Here's the **production deployment checklist** for your WebSocket + notification updates:

---

## Production Deployment Guide

### 1. Update `requirements.txt`
Add Daphne (it's installed locally but missing from requirements):
```
daphne>=4.0,<5.0
```
`channels` and `channels-redis` are already listed.

### 2. Install & start Redis
Your production server (`dzmedilink.duckdns.org`) needs Redis for the channel layer. On your DigitalOcean server:
```bash
sudo apt install redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

### 3. Update production settings

In your production `.env` file on the server, add:
```
REDIS_URL=redis://localhost:6379
```

Then update [core/settings/production.py](core/settings/production.py) — add the Redis channel layer override and CORS for WebSocket origins:

```python
# At the end of production.py, add:

# Use Redis channel layer in production (overrides InMemoryChannelLayer from base.py)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [env("REDIS_URL", default="redis://localhost:6379")],
        },
    },
}
```

### 4. Switch from Gunicorn (WSGI) to Daphne (ASGI)
Your server currently runs WSGI, which **doesn't support WebSockets**. Replace it:

**Before** (likely your current systemd service or process):
```bash
gunicorn core.wsgi:application --bind 0.0.0.0:8000
```

**After:**
```bash
daphne -b 0.0.0.0 -p 8000 core.asgi:application
```

If you use a systemd service file (e.g. `/etc/systemd/system/medilink.service`), update the `ExecStart`:
```ini
[Service]
ExecStart=/path/to/venv/bin/daphne -b 0.0.0.0 -p 8000 core.asgi:application
Environment="DJANGO_SETTINGS_MODULE=core.settings.production"
```

### 5. Configure Nginx for WebSocket proxy
Add WebSocket upgrade headers to your Nginx config for `dzmedilink.duckdns.org`:

```nginx
server {
    server_name dzmedilink.duckdns.org;

    # ... existing SSL config ...

    # Regular HTTP traffic (REST API)
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket traffic
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read
```


## License: unknown
https://github.com/zokeya/gravity_jobcard/blob/36f211385dd63c680e1462c2934ea5c5ae8d299c/.ebextensions/02_nginx.config

```
Here's the **production deployment checklist** for your WebSocket + notification updates:

---

## Production Deployment Guide

### 1. Update `requirements.txt`
Add Daphne (it's installed locally but missing from requirements):
```
daphne>=4.0,<5.0
```
`channels` and `channels-redis` are already listed.

### 2. Install & start Redis
Your production server (`dzmedilink.duckdns.org`) needs Redis for the channel layer. On your DigitalOcean server:
```bash
sudo apt install redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

### 3. Update production settings

In your production `.env` file on the server, add:
```
REDIS_URL=redis://localhost:6379
```

Then update [core/settings/production.py](core/settings/production.py) — add the Redis channel layer override and CORS for WebSocket origins:

```python
# At the end of production.py, add:

# Use Redis channel layer in production (overrides InMemoryChannelLayer from base.py)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [env("REDIS_URL", default="redis://localhost:6379")],
        },
    },
}
```

### 4. Switch from Gunicorn (WSGI) to Daphne (ASGI)
Your server currently runs WSGI, which **doesn't support WebSockets**. Replace it:

**Before** (likely your current systemd service or process):
```bash
gunicorn core.wsgi:application --bind 0.0.0.0:8000
```

**After:**
```bash
daphne -b 0.0.0.0 -p 8000 core.asgi:application
```

If you use a systemd service file (e.g. `/etc/systemd/system/medilink.service`), update the `ExecStart`:
```ini
[Service]
ExecStart=/path/to/venv/bin/daphne -b 0.0.0.0 -p 8000 core.asgi:application
Environment="DJANGO_SETTINGS_MODULE=core.settings.production"
```

### 5. Configure Nginx for WebSocket proxy
Add WebSocket upgrade headers to your Nginx config for `dzmedilink.duckdns.org`:

```nginx
server {
    server_name dzmedilink.duckdns.org;

    # ... existing SSL config ...

    # Regular HTTP traffic (REST API)
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket traffic
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read
```


## License: unknown
https://github.com/zokeya/gravity_jobcard/blob/36f211385dd63c680e1462c2934ea5c5ae8d299c/.ebextensions/02_nginx.config

```
Here's the **production deployment checklist** for your WebSocket + notification updates:

---

## Production Deployment Guide

### 1. Update `requirements.txt`
Add Daphne (it's installed locally but missing from requirements):
```
daphne>=4.0,<5.0
```
`channels` and `channels-redis` are already listed.

### 2. Install & start Redis
Your production server (`dzmedilink.duckdns.org`) needs Redis for the channel layer. On your DigitalOcean server:
```bash
sudo apt install redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

### 3. Update production settings

In your production `.env` file on the server, add:
```
REDIS_URL=redis://localhost:6379
```

Then update [core/settings/production.py](core/settings/production.py) — add the Redis channel layer override and CORS for WebSocket origins:

```python
# At the end of production.py, add:

# Use Redis channel layer in production (overrides InMemoryChannelLayer from base.py)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [env("REDIS_URL", default="redis://localhost:6379")],
        },
    },
}
```

### 4. Switch from Gunicorn (WSGI) to Daphne (ASGI)
Your server currently runs WSGI, which **doesn't support WebSockets**. Replace it:

**Before** (likely your current systemd service or process):
```bash
gunicorn core.wsgi:application --bind 0.0.0.0:8000
```

**After:**
```bash
daphne -b 0.0.0.0 -p 8000 core.asgi:application
```

If you use a systemd service file (e.g. `/etc/systemd/system/medilink.service`), update the `ExecStart`:
```ini
[Service]
ExecStart=/path/to/venv/bin/daphne -b 0.0.0.0 -p 8000 core.asgi:application
Environment="DJANGO_SETTINGS_MODULE=core.settings.production"
```

### 5. Configure Nginx for WebSocket proxy
Add WebSocket upgrade headers to your Nginx config for `dzmedilink.duckdns.org`:

```nginx
server {
    server_name dzmedilink.duckdns.org;

    # ... existing SSL config ...

    # Regular HTTP traffic (REST API)
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket traffic
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read
```


## License: unknown
https://github.com/zokeya/gravity_jobcard/blob/36f211385dd63c680e1462c2934ea5c5ae8d299c/.ebextensions/02_nginx.config

```
Here's the **production deployment checklist** for your WebSocket + notification updates:

---

## Production Deployment Guide

### 1. Update `requirements.txt`
Add Daphne (it's installed locally but missing from requirements):
```
daphne>=4.0,<5.0
```
`channels` and `channels-redis` are already listed.

### 2. Install & start Redis
Your production server (`dzmedilink.duckdns.org`) needs Redis for the channel layer. On your DigitalOcean server:
```bash
sudo apt install redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

### 3. Update production settings

In your production `.env` file on the server, add:
```
REDIS_URL=redis://localhost:6379
```

Then update [core/settings/production.py](core/settings/production.py) — add the Redis channel layer override and CORS for WebSocket origins:

```python
# At the end of production.py, add:

# Use Redis channel layer in production (overrides InMemoryChannelLayer from base.py)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [env("REDIS_URL", default="redis://localhost:6379")],
        },
    },
}
```

### 4. Switch from Gunicorn (WSGI) to Daphne (ASGI)
Your server currently runs WSGI, which **doesn't support WebSockets**. Replace it:

**Before** (likely your current systemd service or process):
```bash
gunicorn core.wsgi:application --bind 0.0.0.0:8000
```

**After:**
```bash
daphne -b 0.0.0.0 -p 8000 core.asgi:application
```

If you use a systemd service file (e.g. `/etc/systemd/system/medilink.service`), update the `ExecStart`:
```ini
[Service]
ExecStart=/path/to/venv/bin/daphne -b 0.0.0.0 -p 8000 core.asgi:application
Environment="DJANGO_SETTINGS_MODULE=core.settings.production"
```

### 5. Configure Nginx for WebSocket proxy
Add WebSocket upgrade headers to your Nginx config for `dzmedilink.duckdns.org`:

```nginx
server {
    server_name dzmedilink.duckdns.org;

    # ... existing SSL config ...

    # Regular HTTP traffic (REST API)
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket traffic
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read
```


## License: unknown
https://github.com/zokeya/gravity_jobcard/blob/36f211385dd63c680e1462c2934ea5c5ae8d299c/.ebextensions/02_nginx.config

```
Here's the **production deployment checklist** for your WebSocket + notification updates:

---

## Production Deployment Guide

### 1. Update `requirements.txt`
Add Daphne (it's installed locally but missing from requirements):
```
daphne>=4.0,<5.0
```
`channels` and `channels-redis` are already listed.

### 2. Install & start Redis
Your production server (`dzmedilink.duckdns.org`) needs Redis for the channel layer. On your DigitalOcean server:
```bash
sudo apt install redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

### 3. Update production settings

In your production `.env` file on the server, add:
```
REDIS_URL=redis://localhost:6379
```

Then update [core/settings/production.py](core/settings/production.py) — add the Redis channel layer override and CORS for WebSocket origins:

```python
# At the end of production.py, add:

# Use Redis channel layer in production (overrides InMemoryChannelLayer from base.py)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [env("REDIS_URL", default="redis://localhost:6379")],
        },
    },
}
```

### 4. Switch from Gunicorn (WSGI) to Daphne (ASGI)
Your server currently runs WSGI, which **doesn't support WebSockets**. Replace it:

**Before** (likely your current systemd service or process):
```bash
gunicorn core.wsgi:application --bind 0.0.0.0:8000
```

**After:**
```bash
daphne -b 0.0.0.0 -p 8000 core.asgi:application
```

If you use a systemd service file (e.g. `/etc/systemd/system/medilink.service`), update the `ExecStart`:
```ini
[Service]
ExecStart=/path/to/venv/bin/daphne -b 0.0.0.0 -p 8000 core.asgi:application
Environment="DJANGO_SETTINGS_MODULE=core.settings.production"
```

### 5. Configure Nginx for WebSocket proxy
Add WebSocket upgrade headers to your Nginx config for `dzmedilink.duckdns.org`:

```nginx
server {
    server_name dzmedilink.duckdns.org;

    # ... existing SSL config ...

    # Regular HTTP traffic (REST API)
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket traffic
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read
```


## License: unknown
https://github.com/zokeya/gravity_jobcard/blob/36f211385dd63c680e1462c2934ea5c5ae8d299c/.ebextensions/02_nginx.config

```
Here's the **production deployment checklist** for your WebSocket + notification updates:

---

## Production Deployment Guide

### 1. Update `requirements.txt`
Add Daphne (it's installed locally but missing from requirements):
```
daphne>=4.0,<5.0
```
`channels` and `channels-redis` are already listed.

### 2. Install & start Redis
Your production server (`dzmedilink.duckdns.org`) needs Redis for the channel layer. On your DigitalOcean server:
```bash
sudo apt install redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

### 3. Update production settings

In your production `.env` file on the server, add:
```
REDIS_URL=redis://localhost:6379
```

Then update [core/settings/production.py](core/settings/production.py) — add the Redis channel layer override and CORS for WebSocket origins:

```python
# At the end of production.py, add:

# Use Redis channel layer in production (overrides InMemoryChannelLayer from base.py)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [env("REDIS_URL", default="redis://localhost:6379")],
        },
    },
}
```

### 4. Switch from Gunicorn (WSGI) to Daphne (ASGI)
Your server currently runs WSGI, which **doesn't support WebSockets**. Replace it:

**Before** (likely your current systemd service or process):
```bash
gunicorn core.wsgi:application --bind 0.0.0.0:8000
```

**After:**
```bash
daphne -b 0.0.0.0 -p 8000 core.asgi:application
```

If you use a systemd service file (e.g. `/etc/systemd/system/medilink.service`), update the `ExecStart`:
```ini
[Service]
ExecStart=/path/to/venv/bin/daphne -b 0.0.0.0 -p 8000 core.asgi:application
Environment="DJANGO_SETTINGS_MODULE=core.settings.production"
```

### 5. Configure Nginx for WebSocket proxy
Add WebSocket upgrade headers to your Nginx config for `dzmedilink.duckdns.org`:

```nginx
server {
    server_name dzmedilink.duckdns.org;

    # ... existing SSL config ...

    # Regular HTTP traffic (REST API)
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket traffic
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read
```


## License: unknown
https://github.com/zokeya/gravity_jobcard/blob/36f211385dd63c680e1462c2934ea5c5ae8d299c/.ebextensions/02_nginx.config

```
Here's the **production deployment checklist** for your WebSocket + notification updates:

---

## Production Deployment Guide

### 1. Update `requirements.txt`
Add Daphne (it's installed locally but missing from requirements):
```
daphne>=4.0,<5.0
```
`channels` and `channels-redis` are already listed.

### 2. Install & start Redis
Your production server (`dzmedilink.duckdns.org`) needs Redis for the channel layer. On your DigitalOcean server:
```bash
sudo apt install redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

### 3. Update production settings

In your production `.env` file on the server, add:
```
REDIS_URL=redis://localhost:6379
```

Then update [core/settings/production.py](core/settings/production.py) — add the Redis channel layer override and CORS for WebSocket origins:

```python
# At the end of production.py, add:

# Use Redis channel layer in production (overrides InMemoryChannelLayer from base.py)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [env("REDIS_URL", default="redis://localhost:6379")],
        },
    },
}
```

### 4. Switch from Gunicorn (WSGI) to Daphne (ASGI)
Your server currently runs WSGI, which **doesn't support WebSockets**. Replace it:

**Before** (likely your current systemd service or process):
```bash
gunicorn core.wsgi:application --bind 0.0.0.0:8000
```

**After:**
```bash
daphne -b 0.0.0.0 -p 8000 core.asgi:application
```

If you use a systemd service file (e.g. `/etc/systemd/system/medilink.service`), update the `ExecStart`:
```ini
[Service]
ExecStart=/path/to/venv/bin/daphne -b 0.0.0.0 -p 8000 core.asgi:application
Environment="DJANGO_SETTINGS_MODULE=core.settings.production"
```

### 5. Configure Nginx for WebSocket proxy
Add WebSocket upgrade headers to your Nginx config for `dzmedilink.duckdns.org`:

```nginx
server {
    server_name dzmedilink.duckdns.org;

    # ... existing SSL config ...

    # Regular HTTP traffic (REST API)
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket traffic
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read
```


## License: unknown
https://github.com/zokeya/gravity_jobcard/blob/36f211385dd63c680e1462c2934ea5c5ae8d299c/.ebextensions/02_nginx.config

```
Here's the **production deployment checklist** for your WebSocket + notification updates:

---

## Production Deployment Guide

### 1. Update `requirements.txt`
Add Daphne (it's installed locally but missing from requirements):
```
daphne>=4.0,<5.0
```
`channels` and `channels-redis` are already listed.

### 2. Install & start Redis
Your production server (`dzmedilink.duckdns.org`) needs Redis for the channel layer. On your DigitalOcean server:
```bash
sudo apt install redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

### 3. Update production settings

In your production `.env` file on the server, add:
```
REDIS_URL=redis://localhost:6379
```

Then update [core/settings/production.py](core/settings/production.py) — add the Redis channel layer override and CORS for WebSocket origins:

```python
# At the end of production.py, add:

# Use Redis channel layer in production (overrides InMemoryChannelLayer from base.py)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [env("REDIS_URL", default="redis://localhost:6379")],
        },
    },
}
```

### 4. Switch from Gunicorn (WSGI) to Daphne (ASGI)
Your server currently runs WSGI, which **doesn't support WebSockets**. Replace it:

**Before** (likely your current systemd service or process):
```bash
gunicorn core.wsgi:application --bind 0.0.0.0:8000
```

**After:**
```bash
daphne -b 0.0.0.0 -p 8000 core.asgi:application
```

If you use a systemd service file (e.g. `/etc/systemd/system/medilink.service`), update the `ExecStart`:
```ini
[Service]
ExecStart=/path/to/venv/bin/daphne -b 0.0.0.0 -p 8000 core.asgi:application
Environment="DJANGO_SETTINGS_MODULE=core.settings.production"
```

### 5. Configure Nginx for WebSocket proxy
Add WebSocket upgrade headers to your Nginx config for `dzmedilink.duckdns.org`:

```nginx
server {
    server_name dzmedilink.duckdns.org;

    # ... existing SSL config ...

    # Regular HTTP traffic (REST API)
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket traffic
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read
```

