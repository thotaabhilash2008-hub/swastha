from pathlib import Path
import re

DIR = Path(__file__).resolve().parent
IMG = re.compile(r'<img\b[^>]*?\bsrc="([^"]*)"', re.I | re.S)
SKIP = {"garden_backup.html", "login.html", "bookmarks.html", "index.html"}

def needs(s: str) -> bool:
    s = (s or "").strip()
    if not s or s.startswith("YOUR_IMAGE_ID"):
        return True
    if re.search(r"\.(jpe?g|png|webp)$", s, re.I) and not s.startswith("http"):
        return True
    if "lh3.googleusercontent.com" in s or "drive.google.com" in s:
        return True
    return False

need = done = wiki = 0
for p in DIR.glob("*.html"):
    if p.name.lower() in SKIP:
        continue
    html = p.read_text(encoding="utf-8", errors="replace")
    srcs = IMG.findall(html)
    if not srcs:
        continue
    if any(needs(s) for s in srcs):
        need += 1
    else:
        done += 1
    if any("wikimedia" in s for s in srcs):
        wiki += 1
print(f"need={need} done={done} with_wikimedia={wiki}")
