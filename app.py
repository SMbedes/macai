#!/usr/bin/env python3
"""Legacy web front-end for OpenAI-compatible chat APIs.

Designed to render in very old browsers (e.g., Netscape Navigator 2.0)
by using plain HTML forms and server-side rendering only.
"""

from __future__ import annotations

import html
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib import error, request
from urllib.parse import parse_qs


HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8080"))
DEFAULT_API_BASE = os.environ.get("OPENAI_API_BASE", "http://127.0.0.1:8000/v1")
DEFAULT_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
DEFAULT_API_KEY = os.environ.get("OPENAI_API_KEY", "")


HTML_PAGE = """<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">
<html>
<head>
<title>MacAI Legacy Client</title>
</head>
<body>
<h1>MacAI Legacy Client</h1>
<p>
This interface is intentionally simple for classic browsers.
Everything is server-rendered. No JavaScript required.
</p>
<hr>
<form method="post" action="/chat">
<p><b>API Base URL:</b><br>
<input type="text" name="api_base" size="60" value="{api_base}"></p>

<p><b>API Key (optional):</b><br>
<input type="password" name="api_key" size="60" value="{api_key}"></p>

<p><b>Model:</b><br>
<input type="text" name="model" size="40" value="{model}"></p>

<p><b>System Prompt (optional):</b><br>
<textarea name="system_prompt" cols="72" rows="4">{system_prompt}</textarea></p>

<p><b>Your Message:</b><br>
<textarea name="user_prompt" cols="72" rows="6">{user_prompt}</textarea></p>

<p><input type="submit" value="Send"></p>
</form>
<hr>
{result}
</body>
</html>
"""


def _escape(value: str) -> str:
    return html.escape(value, quote=True)


def render_result(response_text: str = "", error_text: str = "") -> str:
    if error_text:
        return "<h2>Error</h2><pre>%s</pre>" % _escape(error_text)
    if not response_text:
        return "<p>Ready.</p>"
    return "<h2>Assistant Response</h2><pre>%s</pre>" % _escape(response_text)


def extract_assistant_text(payload: dict) -> str:
    """Extract assistant text from an OpenAI-compatible response payload."""
    choices = payload.get("choices") or []
    if not choices:
        return ""

    choice0 = choices[0]
    message = choice0.get("message") or {}
    content = message.get("content")

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                text = part.get("text", "")
                if isinstance(text, str):
                    parts.append(text)
        return "".join(parts)

    text = choice0.get("text")
    if isinstance(text, str):
        return text

    return ""


def call_openai_compatible(api_base: str, api_key: str, model: str, system_prompt: str, user_prompt: str) -> str:
    endpoint = api_base.rstrip("/") + "/chat/completions"
    messages = []

    if system_prompt.strip():
        messages.append({"role": "system", "content": system_prompt})

    messages.append({"role": "user", "content": user_prompt})

    body = {
        "model": model,
        "messages": messages,
    }

    data = json.dumps(body).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
    }

    if api_key.strip():
        headers["Authorization"] = "Bearer %s" % api_key.strip()

    req = request.Request(endpoint, data=data, headers=headers, method="POST")
    try:
        with request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError("HTTP %s from AI server: %s" % (exc.code, details))
    except error.URLError as exc:
        raise RuntimeError("Could not connect to AI server: %s" % exc)

    try:
        payload = json.loads(raw)
    except ValueError:
        raise RuntimeError("Server returned non-JSON response: %s" % raw)

    output = extract_assistant_text(payload)
    if not output:
        raise RuntimeError("No assistant text found in response payload.")

    return output


class LegacyHandler(BaseHTTPRequestHandler):
    def _send_html(self, content: str) -> None:
        data = content.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802
        if self.path not in ("/", "/chat"):
            self.send_error(404)
            return

        page = HTML_PAGE.format(
            api_base=_escape(DEFAULT_API_BASE),
            api_key=_escape(DEFAULT_API_KEY),
            model=_escape(DEFAULT_MODEL),
            system_prompt="",
            user_prompt="",
            result=render_result(),
        )
        self._send_html(page)

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/chat":
            self.send_error(404)
            return

        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8", errors="replace")
        form = parse_qs(raw, keep_blank_values=True)

        api_base = form.get("api_base", [DEFAULT_API_BASE])[0]
        api_key = form.get("api_key", [DEFAULT_API_KEY])[0]
        model = form.get("model", [DEFAULT_MODEL])[0]
        system_prompt = form.get("system_prompt", [""])[0]
        user_prompt = form.get("user_prompt", [""])[0]

        response_text = ""
        error_text = ""

        if not user_prompt.strip():
            error_text = "Please enter a message."
        else:
            try:
                response_text = call_openai_compatible(api_base, api_key, model, system_prompt, user_prompt)
            except RuntimeError as exc:
                error_text = str(exc)

        page = HTML_PAGE.format(
            api_base=_escape(api_base),
            api_key=_escape(api_key),
            model=_escape(model),
            system_prompt=_escape(system_prompt),
            user_prompt=_escape(user_prompt),
            result=render_result(response_text=response_text, error_text=error_text),
        )
        self._send_html(page)


def main() -> None:
    server = HTTPServer((HOST, PORT), LegacyHandler)
    print("MacAI Legacy Client listening on http://%s:%s" % (HOST, PORT))
    server.serve_forever()


if __name__ == "__main__":
    main()
