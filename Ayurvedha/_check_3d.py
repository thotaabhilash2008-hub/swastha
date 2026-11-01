import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DIR = Path(__file__).resolve().parent
SKIP = {"garden_backup.html", "login.html", "bookmarks.html", "index.html"}

missing_btn = []
missing_modal = []
missing_viewer = []
missing_script = []
has_btn = 0

for p in sorted(DIR.glob("*.html"), key=lambda x: x.name.lower()):
    if p.name.lower() in SKIP:
        continue
    html = p.read_text(encoding="utf-8", errors="replace")
    btn = 'id="open3D"' in html or "id='open3D'" in html
    modal = 'id="viewerModal"' in html
    viewer = "<model-viewer" in html
    script = "model-viewer.min.js" in html
    if btn:
        has_btn += 1
    else:
        missing_btn.append(p.name)
    if not modal:
        missing_modal.append(p.name)
    if not viewer:
        missing_viewer.append(p.name)
    if not script:
        missing_script.append(p.name)

print("HAS_BTN", has_btn)
print("MISSING_BTN", len(missing_btn))
for n in missing_btn:
    print("  ", n)
print("MISSING_MODAL", len(missing_modal))
for n in missing_modal:
    print("  modal", n)
print("MISSING_VIEWER", len(missing_viewer))
for n in missing_viewer:
    print("  viewer", n)
print("MISSING_SCRIPT", len(missing_script))
for n in missing_script:
    print("  script", n)
# intersection
print("NO_BTN_NO_VIEWER", len(set(missing_btn) & set(missing_viewer)))
