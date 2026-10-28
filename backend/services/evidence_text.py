from __future__ import annotations

import json
import logging
import os
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

from services import news_service
from services.evidence_sources import SOURCE_EQS, TYPE_ADHOC, TYPE_GLOBAL, TYPE_NEWS, throttle

logger = logging.getLogger(__name__)

TEXT_DIR = Path(__file__).resolve().parent.parent / "data" / "context_text"
TEXT_VERSION = 1
TEXTS_ENV = "EXPLANATION_TEXTS"

STATUS_OK = "ok"
STATUS_SHORT = "kurz"
STATUS_FAILED = "fehlgeschlagen"

MIN_TEXT_CHARS = 300
MAX_TEXT_CHARS = 40_000
MIN_PARAGRAPH_CHARS = 30
PUBLISHER_INTERVAL_S = 1.0
GOOGLE_INTERVAL_S = 2.0
TIMEOUT_S = 20

GOOGLE_HOST = "news.google.com"
GOOGLE_ARTICLE_URL = "https://news.google.com/rss/articles/{article_id}"
GOOGLE_BATCH_URL = "https://news.google.com/_/DotsSplashUi/data/batchexecute"
_GOOGLE_ID_RE = re.compile(r"news\.google\.com/(?:rss/)?articles/([^/?#]+)")
_SG_RE = re.compile(r'data-n-a-sg="([^"]+)"')
_TS_RE = re.compile(r'data-n-a-ts="([^"]+)"')
_RES_RE = re.compile(r'\\"garturlres\\",\\"((?:[^"\\]|\\\\.)*?)\\"')

Fetcher = Callable[[str], bytes]
Poster = Callable[[str, bytes], bytes]

_DROP_TAGS = ("script", "style", "noscript", "nav", "header", "footer", "aside", "form", "figure", "svg", "iframe",
              "button", "template")
_TEXT_TAGS = ("p", "li", "h1", "h2", "h3", "blockquote")


def http_get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": news_service.USER_AGENT,
                                               "Accept": "text/html,application/xhtml+xml,*/*;q=0.8"})
    with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
        return resp.read()


def http_post(url: str, data: bytes) -> bytes:
    req = urllib.request.Request(url, data=data, headers={
        "User-Agent": news_service.USER_AGENT,
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
    })
    with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
        return resp.read()


def host_of(url: str) -> str:
    return (urllib.parse.urlsplit(url).hostname or "").lower()


def google_article_id(url: Any) -> Optional[str]:
    if not url or not isinstance(url, str):
        return None
    m = _GOOGLE_ID_RE.search(url)
    return m.group(1) if m else None


def google_decode_params(html: Any) -> Optional[Tuple[str, int]]:
    if isinstance(html, bytes):
        html = html.decode("utf-8", "replace")
    if not html or not isinstance(html, str):
        return None
    sg, ts = _SG_RE.search(html), _TS_RE.search(html)
    if not sg or not ts or not ts.group(1).isdigit():
        return None
    return sg.group(1), int(ts.group(1))


def google_decode_payload(article_id: str, timestamp: int, signature: str) -> bytes:
    inner = json.dumps(["garturlreq", [["en-US", "US", ["FINANCE_TOP_INDICES", "WEB_TEST_1_0_0"], None, None, 1, 1,
                                        "US:en", None, 180, None, None, None, None, None, 0, None, None,
                                        [1608992183, 723341000]], "en-US", "US", 1, [2, 3, 4, 8], 1, 0, "655000234",
                                       0, 0, None, 0], article_id, timestamp, signature])
    return ("f.req=" + urllib.parse.quote(json.dumps([[["Fbv4je", inner, None, "generic"]]]))).encode("utf-8")


def parse_google_decode(body: Any) -> Optional[str]:
    if isinstance(body, bytes):
        body = body.decode("utf-8", "replace")
    if not body or not isinstance(body, str):
        return None
    for line in body.splitlines():
        line = line.strip()
        if not line.startswith("["):
            continue
        try:
            parsed = json.loads(line)
        except ValueError:
            continue
        for entry in parsed if isinstance(parsed, list) else []:
            if not (isinstance(entry, list) and len(entry) > 2 and entry[1] == "Fbv4je" and isinstance(entry[2], str)):
                continue
            try:
                inner = json.loads(entry[2])
            except ValueError:
                continue
            if isinstance(inner, list) and len(inner) > 1 and inner[0] == "garturlres" and isinstance(inner[1], str) \
                    and inner[1].startswith(("http://", "https://")):
                return inner[1]
    m = _RES_RE.search(body)
    if m:
        try:
            url = json.loads('"' + m.group(1).replace('\\"', '"') + '"')
        except ValueError:
            return None
        return url if isinstance(url, str) and url.startswith(("http://", "https://")) else None
    return None


def resolve_google_url(url: str, *, fetcher: Optional[Fetcher] = None, poster: Optional[Poster] = None,
                       sleep: Optional[Callable[[float], None]] = None,
                       clock: Optional[Callable[[], float]] = None, interval: Optional[float] = None) -> str:
    article_id = google_article_id(url)
    if article_id is None:
        return url
    get, post = fetcher or http_get, poster or http_post
    gap = GOOGLE_INTERVAL_S if interval is None else interval
    throttle(GOOGLE_HOST, sleep, clock, interval=gap)
    params = google_decode_params(get(GOOGLE_ARTICLE_URL.format(article_id=article_id)))
    if params is None:
        raise ValueError("Google News nennt keine Signatur für den Link (Seitenaufbau geändert?)")
    signature, timestamp = params
    throttle(GOOGLE_HOST, sleep, clock, interval=gap)
    target = parse_google_decode(post(GOOGLE_BATCH_URL, google_decode_payload(article_id, timestamp, signature)))
    if target is None:
        raise ValueError("Google News nennt keine Zieladresse für den Link")
    return target


def extract_main_text(html: Any) -> str:
    from bs4 import BeautifulSoup

    if not html:
        return ""
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(_DROP_TAGS):
        tag.decompose()
    articles = soup.find_all("article")
    root = max(articles, key=lambda a: len(a.get_text(" ", strip=True))) if articles else None
    if root is None or len(root.get_text(" ", strip=True)) < MIN_TEXT_CHARS:
        root = soup.find("main") or soup.body or soup
    seen = set()
    parts: List[str] = []
    for node in root.find_all(_TEXT_TAGS):
        if node.find(_TEXT_TAGS):
            continue
        text = " ".join(node.get_text(" ", strip=True).split())
        if len(text) >= MIN_PARAGRAPH_CHARS and text not in seen:
            seen.add(text)
            parts.append(text)
    return "\n".join(parts)[:MAX_TEXT_CHARS]


def text_path(company_id: int, item_id: str, text_dir: Optional[Path] = None) -> Path:
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", str(item_id)) or "beleg"
    return (text_dir or TEXT_DIR) / str(int(company_id)) / f"{safe}.json"


def load_text(company_id: int, item_id: str, text_dir: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    path = text_path(company_id, item_id, text_dir)
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            record = json.load(fh)
    except (OSError, ValueError) as exc:
        logger.warning("Textspeicher %s nicht lesbar: %s", path, exc)
        return None
    if not isinstance(record, dict) or record.get("id") != item_id or record.get("company_id") != int(company_id):
        return None
    return record


def save_text(record: Dict[str, Any], text_dir: Optional[Path] = None) -> Path:
    path = text_path(record["company_id"], record["id"], text_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(record, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    tmp.replace(path)
    return path


def texts_enabled() -> bool:
    return os.environ.get(TEXTS_ENV, "1").strip().lower() not in ("0", "false", "nein", "off")


def has_usable_text(record: Optional[Dict[str, Any]]) -> bool:
    return bool(record) and record.get("status") in (STATUS_OK, STATUS_SHORT) and bool(record.get("text"))


def attach_texts(company_id: int, items: Iterable[Dict[str, Any]],
                 text_dir: Optional[Path] = None) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    out: List[Dict[str, Any]] = []
    enabled = texts_enabled()
    counts = {"items": 0, "with_text": 0, STATUS_OK: 0, STATUS_SHORT: 0, STATUS_FAILED: 0, "enabled": enabled}
    for item in items:
        counts["items"] += 1
        record = None
        if enabled and item.get("source_type") != TYPE_GLOBAL and item.get("id"):
            record = load_text(company_id, item["id"], text_dir)
        if record is not None and record.get("status") in counts:
            counts[record["status"]] += 1
        if has_usable_text(record):
            counts["with_text"] += 1
            out.append({**item, "text": record["text"], "text_status": record["status"]})
        else:
            out.append(dict(item))
    return out, counts


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _record(company_id: int, item: Dict[str, Any], *, status: str, text: str = "", target_url: Optional[str] = None,
            error: Optional[str] = None, now: Optional[datetime] = None) -> Dict[str, Any]:
    return {
        "version": TEXT_VERSION, "company_id": int(company_id), "id": item.get("id"),
        "source_type": item.get("source_type"), "source_url": item.get("url"), "target_url": target_url,
        "fetched_at": (now or utc_now()).isoformat(timespec="seconds"),
        "status": status, "n_chars": len(text), "error": error, "text": text,
    }


def fetch_item_text(company_id: int, item: Dict[str, Any], *, fetcher: Optional[Fetcher] = None,
                    poster: Optional[Poster] = None, sleep: Optional[Callable[[float], None]] = None,
                    clock: Optional[Callable[[], float]] = None, now: Optional[datetime] = None) -> Dict[str, Any]:
    get = fetcher or http_get
    url = item.get("url") or ""
    source_type = item.get("source_type")
    target: Optional[str] = None
    try:
        if source_type == TYPE_GLOBAL or not url:
            raise ValueError("kein abrufbarer Link")
        if source_type == TYPE_NEWS:
            target = resolve_google_url(url, fetcher=get, poster=poster, sleep=sleep, clock=clock)
        else:
            target = url
        if source_type == TYPE_ADHOC:
            throttle(SOURCE_EQS, sleep, clock)
        else:
            throttle(host_of(target), sleep, clock, interval=PUBLISHER_INTERVAL_S)
        text = extract_main_text(get(target))
        if not text:
            return _record(company_id, item, status=STATUS_FAILED, target_url=target, now=now,
                           error="kein Text auf der Seite gefunden")
        status = STATUS_OK if len(text) >= MIN_TEXT_CHARS else STATUS_SHORT
        return _record(company_id, item, status=status, text=text, target_url=target, now=now)
    except Exception as exc:  # noqa: BLE001
        return _record(company_id, item, status=STATUS_FAILED, target_url=target, now=now,
                       error=f"{type(exc).__name__}: {exc}"[:300])


def text_record(company_id: int, item: Dict[str, Any], *, text_dir: Optional[Path] = None, fetch: bool = True,
                retry_failed: bool = False, fetcher: Optional[Fetcher] = None, poster: Optional[Poster] = None,
                sleep: Optional[Callable[[float], None]] = None, clock: Optional[Callable[[], float]] = None,
                now: Optional[datetime] = None) -> Dict[str, Any]:
    stored = load_text(company_id, item.get("id") or "", text_dir)
    if stored is not None and (stored.get("status") != STATUS_FAILED or not retry_failed):
        return {"record": stored, "fetched_now": False}
    if not fetch:
        return {"record": stored, "fetched_now": False}
    record = fetch_item_text(company_id, item, fetcher=fetcher, poster=poster, sleep=sleep, clock=clock, now=now)
    save_text(record, text_dir)
    return {"record": record, "fetched_now": True}


__all__ = [
    "TEXT_DIR", "TEXT_VERSION", "STATUS_OK", "STATUS_SHORT", "STATUS_FAILED", "MIN_TEXT_CHARS", "MAX_TEXT_CHARS",
    "MIN_PARAGRAPH_CHARS", "PUBLISHER_INTERVAL_S", "GOOGLE_INTERVAL_S", "GOOGLE_HOST", "GOOGLE_ARTICLE_URL", "GOOGLE_BATCH_URL",
    "http_get", "http_post", "host_of", "google_article_id", "google_decode_params", "google_decode_payload",
    "parse_google_decode", "resolve_google_url", "extract_main_text", "text_path", "load_text", "save_text",
    "TEXTS_ENV", "texts_enabled", "has_usable_text", "attach_texts", "fetch_item_text", "text_record", "TYPE_ADHOC",
]
