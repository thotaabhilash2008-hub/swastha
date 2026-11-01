#!/usr/bin/env python3
"""
Fill missing plant image src attributes with Wikimedia Commons URLs.
Resumable: skips pages that already use wikimedia/https plant photos.
"""

from __future__ import annotations

import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# Avoid Windows console Unicode crashes
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

DIR = Path(__file__).resolve().parent
CACHE_PATH = DIR / "_image_url_cache.json"
REPORT_PATH = DIR / "_image_fill_report.json"
SKIP_FILES = {
    "garden_backup.html",
    "login.html",
    "bookmarks.html",
    "index.html",
}
USER_AGENT = (
    "SwasthaPlantBot/1.1 (educational AYUSH gallery; "
    "local student project; contact: swastha-local)"
)
API = "https://commons.wikimedia.org/w/api.php"
SLEEP = 1.2  # polite pacing after 429s

BLOCK_TITLE = re.compile(
    r"(map|logo|flag|icon|svg|diagram|chart|qr|barcode|text|handwriting|"
    r"signature|coin|stamp|medal|coat of arms|emblem|tyrant|bird)",
    re.I,
)

IMG_SRC_RE = re.compile(r'(<img\b[^>]*?\bsrc=")([^"]*)(")', re.I | re.S)


def log(msg: str) -> None:
    print(msg, flush=True)


def api_get(params: dict, retries: int = 6) -> dict:
    params = {**params, "format": "json"}
    qs = urllib.parse.urlencode(params)
    url = f"{API}?{qs}"
    delay = 5.0
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=45) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            last_err = e
            if e.code in (429, 503):
                log(f"  rate-limited ({e.code}), sleeping {delay:.0f}s...")
                time.sleep(delay)
                delay = min(delay * 1.8, 90)
                continue
            raise
        except Exception as e:
            last_err = e
            time.sleep(delay)
            delay = min(delay * 1.5, 60)
    raise RuntimeError(f"API failed after retries: {last_err}")


def clean_sci(raw: str) -> list[str]:
    if not raw:
        return []
    text = raw.replace("\xa0", " ").replace("&nbsp;", " ").replace("&middot;", " ")
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[·•\|/]+", " | ", text)
    text = re.sub(r"[^\x00-\x7F]+", " | ", text)
    text = re.sub(r"\s+", " ", text).strip()
    parts = re.split(r"\s\|\s|\s+[–—\-]\s+", text)
    out: list[str] = []
    for p in parts:
        p = p.strip(" .;")
        if not p:
            continue
        if re.fullmatch(r"[A-Z][a-z]+aceae", p):
            continue
        if p.lower() in {"syn", "synonym", "var", "spp"}:
            continue
        m = re.match(r"^([A-Z][a-z]+(?:\s+[a-z\-]+)?)", p)
        if m:
            out.append(m.group(1))
        elif len(p) > 3 and not re.search(r"\d", p):
            out.append(p)
    seen: set[str] = set()
    uniq: list[str] = []
    for x in out:
        k = x.lower()
        if k not in seen:
            seen.add(k)
            uniq.append(x)
    return uniq


def extract_meta(html: str, filename: str) -> tuple[str, list[str]]:
    title = ""
    m = re.search(r'class="hero-title"[^>]*>(.*?)</', html, re.S | re.I)
    if m:
        title = re.sub(r"<[^>]+>", "", m.group(1)).strip()
    if not title:
        m = re.search(r"<title>(.*?)</title>", html, re.I)
        if m:
            title = m.group(1).split("—")[0].split("|")[0].strip()
    if not title:
        title = Path(filename).stem.replace("_", " ").split("  ")[0].strip()

    sci_raw = ""
    m = re.search(r'class="hero-sci"[^>]*>(.*?)</', html, re.S | re.I)
    if m:
        sci_raw = m.group(1)

    subtitle = ""
    m = re.search(r'class="hero-subtitle"[^>]*>(.*?)</', html, re.S | re.I)
    if m:
        subtitle = re.sub(r"<[^>]+>", "", m.group(1)).strip()
        subtitle = re.split(r"[—\-–]", subtitle)[0].strip()

    queries = clean_sci(sci_raw)
    for extra in (title, subtitle):
        if (
            extra
            and len(extra) > 2
            and extra.lower() not in {q.lower() for q in queries}
            and extra.lower() not in {"plant", "herb", "tree", "flower"}
            and len(extra) < 40
        ):
            queries.append(extra)
    # Cap query attempts to reduce rate-limit pressure
    return title, queries[:3]


def search_commons(query: str, limit: int = 8) -> list[str]:
    if re.match(r"^[A-Z][a-z]+\s+[a-z\-]+$", query.strip()):
        srsearch = f'"{query.strip()}"'
    else:
        srsearch = f"{query.strip()} plant"

    data = api_get(
        {
            "action": "query",
            "list": "search",
            "srsearch": srsearch,
            "srnamespace": "6",
            "srlimit": str(limit),
        }
    )
    titles: list[str] = []
    for hit in data.get("query", {}).get("search", []):
        t = hit.get("title", "")
        if not t.startswith("File:"):
            continue
        if BLOCK_TITLE.search(t):
            continue
        if not re.search(r"\.(jpe?g|png|webp)$", t, re.I):
            continue
        titles.append(t)
    return titles


def file_urls(titles: list[str], width: int = 1280) -> list[str]:
    if not titles:
        return []
    data = api_get(
        {
            "action": "query",
            "titles": "|".join(titles[:8]),
            "prop": "imageinfo",
            "iiprop": "url|mime|size",
            "iiurlwidth": str(width),
        }
    )
    pages = data.get("query", {}).get("pages", {})
    by_title = {p.get("title"): p for p in pages.values()}
    urls: list[str] = []
    for t in titles:
        page = by_title.get(t)
        if not page:
            continue
        info = (page.get("imageinfo") or [None])[0]
        if not info:
            continue
        mime = (info.get("mime") or "").lower()
        if not mime.startswith("image/"):
            continue
        url = info.get("thumburl") or info.get("url")
        if url:
            urls.append(url.split("?")[0])
    return urls


def rank_titles(titles: list[str], query: str) -> list[str]:
    tokens = [t.lower() for t in re.findall(r"[A-Za-z]{4,}", query)]

    def score(title: str) -> int:
        low = title.lower()
        s = sum(3 for tok in tokens if tok in low)
        if any(w in low for w in ("flower", "plant", "leaf", "fruit")):
            s += 1
        return s

    return sorted(titles, key=score, reverse=True)


def find_two_images(queries: list[str], cache: dict) -> list[str]:
    collected: list[str] = []
    seen: set[str] = set()
    binomials = [q for q in queries if re.match(r"^[A-Z][a-z]+\s+[a-z\-]+$", q.strip())]
    others = [q for q in queries if q not in binomials]
    ordered = binomials + others

    for q in ordered:
        key = q.lower().strip()
        if not key or len(key) < 3:
            continue
        if key in cache and cache[key]:
            for u in cache[key]:
                if u not in seen:
                    seen.add(u)
                    collected.append(u)
            if len(collected) >= 2:
                return collected[:2]
            continue

        try:
            titles = search_commons(q)
            time.sleep(SLEEP)
            titles = rank_titles(titles, q)
            genus = q.strip().split()[0].lower() if " " in q.strip() else ""
            if genus and re.match(r"^[A-Z][a-z]+\s+[a-z\-]+$", q.strip()):
                filtered = [t for t in titles if genus in t.lower()]
                if filtered:
                    titles = filtered
            urls = file_urls(titles)
            time.sleep(SLEEP)
        except Exception as e:
            log(f"  search failed for '{q}': {e}")
            cache[key] = []
            time.sleep(SLEEP)
            continue

        cache[key] = urls
        for u in urls:
            if u not in seen:
                seen.add(u)
                collected.append(u)
        if len(collected) >= 2:
            return collected[:2]

    return collected[:2]


def needs_replace(src: str) -> bool:
    s = (src or "").strip()
    if not s:
        return True
    if s.startswith("YOUR_IMAGE_ID"):
        return True
    if re.search(r"\.(jpe?g|png|webp)$", s, re.I) and not s.startswith("http"):
        return True
    if "lh3.googleusercontent.com" in s or "drive.google.com" in s:
        return True
    return False


def replace_plant_images(html: str, urls: list[str]) -> tuple[str, int]:
    if not urls:
        return html, 0
    idx = 0
    replaced = 0

    def repl(m: re.Match) -> str:
        nonlocal idx, replaced
        src = m.group(2)
        if not needs_replace(src):
            return m.group(0)
        url = urls[idx % len(urls)]
        idx += 1
        replaced += 1
        return f"{m.group(1)}{url}{m.group(3)}"

    return IMG_SRC_RE.sub(repl, html), replaced


def save_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    cache: dict = {}
    if CACHE_PATH.exists():
        try:
            cache = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        except Exception:
            cache = {}

    report = {"updated": [], "skipped": [], "failed": []}
    files = sorted(DIR.glob("*.html"), key=lambda p: p.name.lower())

    for path in files:
        if path.name.lower() in SKIP_FILES:
            report["skipped"].append({"file": path.name, "reason": "special page"})
            continue

        html = path.read_text(encoding="utf-8", errors="replace")
        if 'class="hero-title"' not in html and "model-viewer" not in html:
            report["skipped"].append({"file": path.name, "reason": "not herb page"})
            continue

        srcs = [m.group(2) for m in IMG_SRC_RE.finditer(html)]
        need = [s for s in srcs if needs_replace(s)]
        if not need:
            report["skipped"].append({"file": path.name, "reason": "already has remote images"})
            continue

        title, queries = extract_meta(html, path.name)
        log(f"\n{path.name}: {title} | queries={queries}")
        urls = find_two_images(queries, cache)
        if not urls:
            report["failed"].append({"file": path.name, "title": title, "queries": queries})
            log("  NO IMAGES FOUND")
            save_json(CACHE_PATH, cache)
            save_json(REPORT_PATH, report)
            continue

        new_html, n = replace_plant_images(html, urls)
        if n == 0:
            report["skipped"].append({"file": path.name, "reason": "no replaceable imgs"})
            continue

        path.write_text(new_html, encoding="utf-8")
        report["updated"].append(
            {"file": path.name, "title": title, "replaced": n, "urls": urls}
        )
        log(f"  replaced {n} -> {urls[0][:90]}...")
        save_json(CACHE_PATH, cache)
        save_json(REPORT_PATH, report)

    log(
        f"\nDone. updated={len(report['updated'])} "
        f"failed={len(report['failed'])} skipped={len(report['skipped'])}"
    )
    log(f"Report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
