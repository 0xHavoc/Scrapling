# Scrapling Web UI Example

This example adds a lightweight single-page frontend under `examples/webui/frontend/`.

## Features

- Inputs for URL, fetcher type, timeout, headers/cookies/params, and selector.
- Calls backend endpoints:
  - `POST /api/fetch`
  - `POST /api/extract`
- Output tabs:
  - Extracted Data
  - Raw HTML/Text
  - Request Logs
- Loading/progress and user-friendly error messages.
- Copy and download actions for current output tab.
- Basic client-side validation for URL, timeout, and JSON fields.

## Run locally

Serve the `frontend` folder with any static file server and make sure your backend serves `/api/fetch` and `/api/extract` on the same origin.

For example:

```bash
python -m http.server 8080 -d examples/webui/frontend
```

Then open <http://localhost:8080>.
