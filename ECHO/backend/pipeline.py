"""Resumable comment ingestion. Python 3.9+, standard library only."""
import argparse
import hashlib
import json
import os
import re
import sqlite3
import time
import unicodedata
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit, parse_qsl, urlunsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler

class PipelineError(Exception):
    pass

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def pick(obj, path, default=None):
    if not path:
        return default
    for part in path.split("."):
        if not isinstance(obj, dict) or part not in obj:
            return default
        obj = obj[part]
    return obj

def clean(text):
    # Keep the untouched original; clean text is an additional representation.
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"\[(?:微笑|捂脸|笑哭|赞|比心|流泪|大笑|呲牙|发怒|爱心|鼓掌)\]", "", text)
    text = "".join(c for c in text if not (
        0x1F000 <= ord(c) <= 0x1FAFF or 0x2600 <= ord(c) <= 0x27BF
        or ord(c) in (0x200D, 0xFE0F, 0x20E3)))
    text = re.sub(r"(?<!\w)@[^\s@]+", "", text)
    text = re.sub(r"(?<!\d)1[3-9]\d{9}(?!\d)", "[手机号]", text)
    text = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[邮箱]", text)
    text = " ".join(text.split())
    useful = bool(re.search(r"[\u3400-\u9fffA-Za-z0-9]", text))
    return text, None if useful else "empty_or_expression_only"

def request_json(url, method="GET", body=None, headers=None, retries=3):
    parsed = urlsplit(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username or parsed.password:
        raise PipelineError("Invalid HTTP endpoint (embedded credentials are forbidden)")
    if parsed.scheme != "https" and parsed.hostname not in ("localhost", "127.0.0.1", "::1"):
        raise PipelineError("Remote endpoints must use HTTPS")
    data = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
    request_headers = {"Accept": "application/json", **(headers or {})}
    if data is not None:
        request_headers["Content-Type"] = "application/json"
    for attempt in range(retries + 1):
        try:
            req = Request(url, data=data, headers=request_headers, method=method)
            with build_opener(NoRedirect).open(req, timeout=30) as response:
                raw = response.read(8 * 1024 * 1024 + 1)
                if len(raw) > 8 * 1024 * 1024:
                    raise PipelineError("Response exceeds 8 MiB")
                return json.loads(raw.decode("utf-8")) if raw else {}
        except HTTPError as exc:
            status = exc.code
            if status not in (429, 500, 502, 503, 504) or attempt == retries:
                raise PipelineError("HTTP " + str(status) + " (response body omitted)") from None
            delay = min(30, 2 ** attempt)
            retry_after = exc.headers.get("Retry-After", "")
            if retry_after.isdigit():
                delay = min(60, int(retry_after))
        except (URLError, TimeoutError, ConnectionError, OSError):
            if attempt == retries:
                raise PipelineError("Network request failed (details omitted)") from None
            delay = min(30, 2 ** attempt)
        except (ValueError, UnicodeError):
            raise PipelineError("Endpoint returned invalid JSON") from None
        time.sleep(delay)
    raise PipelineError("Retry limit reached")

def connect(path):
    db = sqlite3.connect(path)
    db.execute("PRAGMA journal_mode=WAL")
    db.executescript("""
    CREATE TABLE IF NOT EXISTS comments(
        id TEXT PRIMARY KEY, payload TEXT NOT NULL, excluded TEXT,
        state TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0,
        last_error TEXT);
    CREATE TABLE IF NOT EXISTS checkpoints(
        source TEXT PRIMARY KEY, cursor TEXT, done INTEGER NOT NULL);
    """)
    return db

def source_key(source):
    # Product assignments and field mappings are part of the ingestion identity.
    return hashlib.sha256(json.dumps(source, sort_keys=True).encode()).hexdigest()

def normalize(item, source):
    fields = source["fields"]
    raw = pick(item, fields["text"])
    if not isinstance(raw, str):
        raise PipelineError("Comment text field missing or not a string; checkpoint not advanced")
    comment_id = pick(item, fields.get("id"))
    if comment_id is None or str(comment_id).strip() == "":
        raise PipelineError("Stable comment ID required; checkpoint not advanced")
    video_id = pick(item, fields.get("video_id"), source.get("video_id", ""))
    cleaned, excluded = clean(raw)
    identity = [source.get("platform", "douyin"), source["product"], str(video_id), str(comment_id)]
    key = hashlib.sha256(json.dumps(identity, ensure_ascii=False).encode()).hexdigest()
    return key, {
        "schema_version": 1,
        "external_id": key,
        "platform": identity[0],
        "product": source["product"],
        "comment_id": str(comment_id),
        "video_id": str(video_id),
        "video_url": pick(item, fields.get("video_url"), source.get("video_url")),
        "created_at": pick(item, fields.get("created_at")),
        "likes": pick(item, fields.get("likes")),
        "original_text": raw,
        "cleaned_text": cleaned,
        "excluded_reason": excluded,
        "analysis_status": "pending"
    }, excluded

def ingest(db, source, base):
    key = source_key(source)
    saved = db.execute("SELECT cursor,done FROM checkpoints WHERE source=?", (key,)).fetchone()
    if saved and saved[1]:
        return
    cursor = json.loads(saved[0]) if saved else source.get("initial_cursor", 0)
    headers = {}
    cookie_env = source.get("cookie_env")
    if cookie_env:
        cookie = os.environ.get(cookie_env)
        if not cookie:
            raise PipelineError("Required crawler cookie environment variable is not set")
        headers[source.get("cookie_header", "Cookie")] = cookie
    for _ in range(source.get("max_pages_per_run", 100)):
        if source["type"] == "file":
            page = json.loads((base / source["path"]).read_text(encoding="utf-8-sig"))
            more, next_cursor = False, None
        elif source["type"] == "http":
            params = dict(source.get("params", {}))
            params[source.get("cursor_param", "cursor")] = cursor
            method = source.get("method", "GET").upper()
            url = source["url"]
            if method == "GET":
                parts = urlsplit(url)
                query = dict(parse_qsl(parts.query))
                query.update(params)
                url = urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), ""))
                page = request_json(url, headers=headers)
            elif method == "POST":
                page = request_json(url, method, params, headers)
            else:
                raise PipelineError("Crawler method must be GET or POST")
            more = pick(page, source["has_more_path"])
            if more not in (True, False, 0, 1) or more is None:
                raise PipelineError("has_more must be a boolean or 0/1")
            next_cursor = pick(page, source["next_cursor_path"])
            if more and (next_cursor is None or next_cursor == cursor):
                raise PipelineError("Invalid or non-advancing pagination cursor")
        else:
            raise PipelineError("Unsupported source type")
        rows = pick(page, source["items_path"])
        if not isinstance(rows, list):
            raise PipelineError("Comment list field missing; checkpoint not advanced")
        if more and not rows:
            raise PipelineError("Empty page with has_more; checkpoint not advanced")
        normalized = [normalize(row, source) for row in rows]
        with db:
            for identifier, payload, excluded in normalized:
                db.execute("INSERT OR IGNORE INTO comments(id,payload,excluded,state) VALUES(?,?,?,?)",
                    (identifier, json.dumps(payload, ensure_ascii=False), excluded,
                     "excluded" if excluded else "pending"))
            db.execute("INSERT OR REPLACE INTO checkpoints VALUES(?,?,?)",
                       (key, json.dumps(next_cursor), int(not more)))
        if not more:
            return
        cursor = next_cursor
        time.sleep(source.get("page_delay_seconds", 1))

def deliver(db, sink):
    if not sink or not sink.get("url"):
        return
    token_env = sink.get("token_env")
    token = os.environ.get(token_env) if token_env else None
    if token_env and not token:
        raise PipelineError("Workbench token environment variable is not set")
    headers = {"Authorization": "Bearer " + token} if token else {}
    for identifier, stored in db.execute(
        "SELECT id,payload FROM comments WHERE state IN ('pending','failed') ORDER BY rowid"
    ).fetchall():
        payload = json.loads(stored)
        if not sink.get("include_original_text", False):
            payload.pop("original_text", None)
        try:
            result = request_json(sink["url"], "POST", payload,
                                  {**headers, "Idempotency-Key": identifier})
            if not isinstance(result, dict) or result.get("accepted") is not True or result.get("external_id") != identifier:
                raise PipelineError("Workbench did not acknowledge this external_id")
            state, error = "delivered", None
        except PipelineError as exc:
            state, error = "failed", str(exc)
        with db:
            db.execute("UPDATE comments SET state=?, attempts=attempts+1,last_error=? WHERE id=?",
                       (state, error, identifier))
        # Avoid hammering an endpoint with a broken contract or expired credentials.
        if error:
            raise PipelineError(error)

def run(config_path, retry_only=False):
    config_path = Path(config_path).resolve()
    config = json.loads(config_path.read_text(encoding="utf-8-sig"))
    db_path = config_path.parent / config.get("database", "state.sqlite3")
    db = connect(db_path)
    try:
        if not retry_only:
            for source in config["sources"]:
                ingest(db, source, config_path.parent)
        deliver(db, config.get("sink"))
        return dict(db.execute("SELECT state,COUNT(*) FROM comments GROUP BY state").fetchall())
    finally:
        db.close()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config")
    parser.add_argument("--retry-only", action="store_true")
    args = parser.parse_args()
    try:
        print(json.dumps(run(args.config, args.retry_only), ensure_ascii=False))
    except (PipelineError, KeyError, ValueError, OSError, sqlite3.Error) as exc:
        # Never dump URLs, response bodies, environment variables or comment payloads.
        print("Pipeline stopped: " + (str(exc) if isinstance(exc, PipelineError) else type(exc).__name__))
        raise SystemExit(1)

if __name__ == "__main__":
    main()

