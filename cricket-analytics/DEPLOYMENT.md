# Deployment Guide
## Cricket Analytics AI Agent — Nginx + SSL + Public Access

This guide covers deploying the app so it is accessible over HTTPS —
both on your local network and publicly via ngrok.

---

## Architecture

```
Internet
    ↓
  ngrok (free public HTTPS URL)
    ↓
Nginx (port 443 — SSL termination)
    ↓
FastAPI / uvicorn (port 8000 — local only)
    ↓
PostgreSQL (port 5432 — local only)
```

---

## Prerequisites

Make sure these are installed before starting:

| Tool | Purpose | Install |
|---|---|---|
| Python 3.10+ | Run FastAPI | python.org |
| PostgreSQL 14+ | Database | enterprisedb.com |
| Node.js 18+ | Build React frontend | nodejs.org |
| Homebrew | Mac package manager | brew.sh |
| Nginx | Web server / reverse proxy | via Homebrew |
| ngrok | Public HTTPS tunnel | ngrok.com |

---

## Step 1 — Install Nginx

```bash
brew install nginx
```

Verify:
```bash
nginx -v
```

---

## Step 2 — Generate a self-signed SSL certificate

This gives you HTTPS. Browsers will show a security warning since it
is not signed by a certificate authority — this is expected without a
real domain name. Click "Advanced → Proceed" to continue.

```bash
mkdir -p ~/.ssl/cricket
cd ~/.ssl/cricket

openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout cricket.key \
  -out cricket.crt \
  -subj "/C=IN/ST=Maharashtra/L=Nagpur/O=CricketAnalytics/CN=localhost"
```

This creates two files:
- `~/.ssl/cricket/cricket.crt` — the certificate
- `~/.ssl/cricket/cricket.key` — the private key

---

## Step 3 — Configure Nginx

Find your Nginx config directory:
```bash
brew --prefix nginx
```

It is usually at `/opt/homebrew/etc/nginx/` (Apple Silicon Mac)
or `/usr/local/etc/nginx/` (Intel Mac).

Replace the contents of `nginx.conf` with the config below.
First check which path applies to you:

```bash
ls /opt/homebrew/etc/nginx/nginx.conf 2>/dev/null || ls /usr/local/etc/nginx/nginx.conf
```

Then open the file:
```bash
# Apple Silicon:
open /opt/homebrew/etc/nginx/nginx.conf

# Intel Mac:
open /usr/local/etc/nginx/nginx.conf
```

Replace the entire file contents with this:

```nginx
worker_processes 1;

events {
    worker_connections 1024;
}

http {
    include       mime.types;
    default_type  application/octet-stream;
    sendfile      on;
    keepalive_timeout 65;

    # Redirect HTTP → HTTPS
    server {
        listen 80;
        server_name localhost;
        return 301 https://$host$request_uri;
    }

    # HTTPS server
    server {
        listen 443 ssl;
        server_name localhost;

        ssl_certificate     /Users/YOUR_MAC_USERNAME/.ssl/cricket/cricket.crt;
        ssl_certificate_key /Users/YOUR_MAC_USERNAME/.ssl/cricket/cricket.key;
        ssl_protocols       TLSv1.2 TLSv1.3;
        ssl_ciphers         HIGH:!aNULL:!MD5;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=31536000" always;

        # Proxy all requests to FastAPI
        location / {
            proxy_pass         http://127.0.0.1:8000;
            proxy_set_header   Host $host;
            proxy_set_header   X-Real-IP $remote_addr;
            proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header   X-Forwarded-Proto $scheme;
            proxy_read_timeout 120s;
            proxy_buffering    off;
        }
    }
}
```

**Important:** Replace `YOUR_MAC_USERNAME` with your actual Mac username.
You can find it by running: `whoami`

---

## Step 4 — Test and start Nginx

Test the config is valid:
```bash
sudo nginx -t
```

You should see:
```
nginx: configuration file ... syntax is ok
nginx: configuration file ... test is successful
```

Start Nginx:
```bash
sudo nginx
```

If it is already running and you made changes:
```bash
sudo nginx -s reload
```

---

## Step 5 — Build the React frontend

```bash
cd frontend
npm run build
cd ..
```

---

## Step 6 — Start the FastAPI backend

```bash
uvicorn web_app:app --host 127.0.0.1 --port 8000
```

Note: `127.0.0.1` (not `0.0.0.0`) — FastAPI only listens locally.
Nginx handles all external traffic and forwards to it.

---

## Step 7 — Test locally

Open your browser and go to:
```
https://localhost
```

You will see a browser security warning — click **Advanced → Proceed to localhost**.
The app should load over HTTPS.

---

## Step 8 — Make it publicly accessible via ngrok

### Install ngrok
```bash
brew install ngrok/ngrok/ngrok
```

### Sign up (free)
Go to **ngrok.com**, create a free account, then copy your auth token
from the dashboard and run:
```bash
ngrok config add-authtoken YOUR_NGROK_TOKEN
```

### Start the tunnel
```bash
ngrok http 8000
```

ngrok will show output like:
```
Forwarding  https://abc123.ngrok-free.app → http://localhost:8000
```

That `https://abc123.ngrok-free.app` URL is your public HTTPS link.
Share it with Sujit — anyone with the link can access the app.

> **Note:** The free ngrok URL changes every time you restart ngrok.
> To get a fixed URL, upgrade to ngrok's paid plan or use a real domain.

---

## Running everything together

Open three terminal tabs in VS Code (click + in the terminal panel):

**Tab 1 — FastAPI backend:**
```bash
cd ~/path/to/cricket-analytics
uvicorn web_app:app --host 127.0.0.1 --port 8000
```

**Tab 2 — Nginx (if not already running):**
```bash
sudo nginx
```

**Tab 3 — ngrok tunnel:**
```bash
ngrok http 8000
```

Copy the `https://...ngrok-free.app` URL from Tab 3 and share it.

---

## Stopping everything

```bash
# Stop FastAPI — press Ctrl+C in Tab 1

# Stop Nginx
sudo nginx -s stop

# Stop ngrok — press Ctrl+C in Tab 3
```

---

## Upgrading to a real domain + Let's Encrypt SSL (future)

When you have a real domain (e.g. `cricket.yourdomain.com`), replace
the self-signed certificate with a free Let's Encrypt certificate:

```bash
brew install certbot
sudo certbot certonly --standalone -d cricket.yourdomain.com
```

Then update `nginx.conf` to point to the Let's Encrypt certificates:
```nginx
ssl_certificate     /etc/letsencrypt/live/cricket.yourdomain.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/cricket.yourdomain.com/privkey.pem;
```

Let's Encrypt certificates auto-renew every 90 days.

---

## Troubleshooting

**"Address already in use" on port 80/443**
```bash
sudo nginx -s stop
sudo nginx
```

**"Permission denied" on port 80/443**
Nginx needs sudo to bind to ports below 1024 on macOS.
Always use `sudo nginx` and `sudo nginx -s reload`.

**ngrok shows "connection refused"**
Make sure uvicorn is running on port 8000 before starting ngrok.

**Browser still shows insecure warning**
This is expected with a self-signed certificate.
Click Advanced → Proceed to continue. This warning goes away
when you switch to a real domain with Let's Encrypt.

**"502 Bad Gateway" in browser**
FastAPI is not running. Start uvicorn first, then reload nginx.

**Changes not showing after rebuild**
```bash
cd frontend && npm run build && cd ..
```
Then hard-refresh the browser (Cmd+Shift+R).
