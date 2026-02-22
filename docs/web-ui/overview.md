# Web UI Deployment Overview

This page describes a practical setup for running a Scrapling-backed Web UI with a Python backend API and a separate frontend app.

!!! warning "Security warning"
    Do **not** expose scraping endpoints publicly without authentication, authorization checks, and strict rate limits. Open scraping APIs are commonly abused for credential stuffing, proxy abuse, and denial-of-service traffic.

## Architecture

A common local/production layout:

- **Backend API**: Python service that executes scraping jobs through Scrapling.
- **Frontend**: Browser UI that submits jobs and displays progress/results.
- **Reverse proxy**: Optional entrypoint (Nginx, Traefik, Caddy, Cloudflare) that handles TLS, routing, and security headers.

## Installation

### Backend dependencies

Install the package itself:

```bash
pip install scrapling
```

If your backend uses fetchers/browsers:

```bash
pip install "scrapling[fetchers]"
scrapling install
```

Optional backend extras for a Web API stack:

```bash
pip install "scrapling[web]"
```

### Frontend dependencies

This depends on your UI stack. Example for Node-based frontends:

```bash
cd frontend
npm install
```

## Local development

### Run backend locally

Example (FastAPI-style command):

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Run frontend locally

Example (Vite-style command):

```bash
cd frontend
npm run dev -- --host 0.0.0.0 --port 5173
```

Configure your frontend API base URL to `http://localhost:8000` (or your local reverse proxy URL).

## Production notes

### Reverse proxy

Recommended production pattern:

- Terminate TLS at reverse proxy.
- Route `/api/*` to backend, and `/` to frontend static/app server.
- Add timeouts suitable for long scraping operations.
- Enable request-size limits and bot protections where possible.

### CORS

Keep CORS narrow:

- Allow only known frontend origin(s).
- Do not use wildcard CORS with credentials.
- Restrict methods and headers to what is required.

### Authentication and authorization

Use strong auth in front of scraping endpoints:

- Session or token-based auth (JWT/OAuth/etc.).
- Per-user/team authorization checks for job/result access.
- API keys only when rotation/revocation is in place.

### Rate limiting and abuse prevention

At minimum:

- Per-IP and per-account rate limits.
- Concurrent-job limits per user.
- Queue limits and bounded retries.
- Audit logging and anomaly alerts.

!!! danger "Do not run an open scraper API"
    If endpoints are publicly reachable without auth/rate limits, they will likely be abused quickly and can incur legal, reputational, and infrastructure risks.

## Docker Compose example

See `examples/webui/docker-compose.yml` for a baseline backend + frontend setup.
