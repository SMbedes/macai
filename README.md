# MacAI Legacy Web Client

A tiny server-rendered chat front-end intended for very old browsers like
**Netscape Navigator 2.0** running on classic PowerPC Macs.

## Why this works for legacy browsers

- Plain HTML form submission (`GET` + `POST`), no JavaScript required.
- No CSS or modern layout assumptions.
- Server-side API call to your OpenAI-compatible endpoint.

## Requirements

- Python 3.8+
- Reachable OpenAI-compatible API server

## Run

```bash
python3 app.py
```

Then open:

- `http://<server-ip>:8080/`

## Optional environment variables

- `HOST` (default: `0.0.0.0`)
- `PORT` (default: `8080`)
- `OPENAI_API_BASE` (default: `http://127.0.0.1:8000/v1`)
- `OPENAI_MODEL` (default: `gpt-4o-mini`)
- `OPENAI_API_KEY` (default: empty)

## Notes for old Macs

Because old browsers may not support modern TLS/ciphers, a common setup is:

1. Run this app on a newer machine on your LAN.
2. Access it from the Power Mac in Netscape.
3. Let this app (new machine) talk to your AI server over modern HTTPS.

This keeps the browser side simple and compatible.
