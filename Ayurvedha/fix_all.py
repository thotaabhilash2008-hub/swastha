"""
Fix script for 3 issues across all plant HTML pages:
1. Filter checkbox highlight (only in index.html)
2. View in 3D button visibility (ensure it's visible, style it consistently)
3. Button color consistency - make btn-bookmark match #open3D style
"""

import os
import re

AYUSH_DIR = r"c:\Users\manis\Downloads\AYUSH\AYUSH\Ayurvedha"

SKIP_FILES = {'index.html', 'Garden_backup.html', 'bookmarks.html', 'login.html', 'fix_all.py'}

def fix_plant_file(filepath, filename):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    original = content
    changes = []

    # ── FIX 3: Make btn-bookmark match green style ──────────────────────────
    # Replace gold-bordered bookmark button style with green style
    # Pattern: .btn-bookmark { ... color: var(--gold) ... }
    # New style: green background matching #open3D
    
    # Old btn-bookmark style (various forms)
    old_bookmark_patterns = [
        # Multi-line version in Agastya-style files
        r'\.btn-bookmark\s*\{[^}]+\}',
        # The hover too
        r'\.btn-bookmark:hover\s*\{[^}]+\}',
        r'\.btn-bookmark\.saved\s*\{[^}]+\}',
        r'\.btn-bookmark:disabled\s*\{[^}]+\}',
    ]
    
    NEW_BOOKMARK_STYLE = '''    .btn-bookmark { display: inline-flex; align-items: center; gap: 8px; background: var(--forest); border: none; color: #fff; font-family: 'Jost', sans-serif; font-size: 10px; font-weight: 300; letter-spacing: 3px; text-transform: uppercase; padding: 10px 20px; cursor: pointer; border-radius: 0; transition: background 0.3s, color 0.3s; position: relative; z-index: 2; }
    .btn-bookmark:hover { background: var(--gold); color: var(--deep); }
    .btn-bookmark.saved { background: var(--deep); color: var(--cream); }
    .btn-bookmark:disabled { opacity: 0.6; cursor: wait; }'''
    
    NEW_BOOKMARK_STYLE_MINIFIED = '''.btn-bookmark{display:inline-flex;align-items:center;gap:8px;background:var(--forest);border:none;color:#fff;font-family:'Jost',sans-serif;font-size:10px;font-weight:300;letter-spacing:3px;text-transform:uppercase;padding:10px 20px;cursor:pointer;border-radius:0;transition:background .3s,color .3s;position:relative;z-index:2}
.btn-bookmark:hover{background:var(--gold);color:var(--deep)}
.btn-bookmark.saved{background:var(--deep);color:var(--cream)}
.btn-bookmark:disabled{opacity:.6;cursor:wait}'''

    # ── FIX 2: Ensure #open3D button is always visible ──────────────────────
    # The button should be visible. Make sure it has proper z-index and position
    # Also add font-family: 'Jost' to match overall theme
    
    # Check if open3D style uses font-family
    if '#open3D' in content and "font-family" not in content.split('#open3D')[1].split('}')[0]:
        # Add font-family to open3D
        content = content.replace(
            '#open3D{position:fixed;top:25px;right:30px;padding:10px 18px;font-size:11px;letter-spacing:2px;text-transform:uppercase;background:var(--forest);color:#fff;border:none;cursor:pointer;z-index:1000;transition:.3s}',
            "#open3D{position:fixed;top:25px;right:30px;padding:10px 18px;font-size:11px;letter-spacing:2px;text-transform:uppercase;font-family:'Jost',sans-serif;background:var(--forest);color:#fff;border:none;cursor:pointer;z-index:1000;transition:.3s}"
        )
        if content != original:
            changes.append('Added font-family to #open3D')

    # ── Apply bookmark style fix ─────────────────────────────────────────────
    # Detect which format this file uses (minified vs pretty)
    is_minified = '.btn-bookmark{' in content
    
    if is_minified:
        # Minified format (older files like arjuna.html)
        # Match full btn-bookmark block including hover/saved/disabled
        pattern = r'\.btn-bookmark\{[^}]+\}(?:\s*\.btn-bookmark:[^{]+\{[^}]+\})*'
        
        # Find the btn-bookmark section
        if '.btn-bookmark{' in content:
            # Build replacement
            new_style = '''.btn-bookmark{display:inline-flex;align-items:center;gap:8px;background:var(--forest);border:none;color:#fff;font-family:'Jost',sans-serif;font-size:10px;font-weight:300;letter-spacing:3px;text-transform:uppercase;padding:10px 20px;cursor:pointer;border-radius:0;transition:background .3s,color .3s;position:relative;z-index:2}
.btn-bookmark:hover{background:var(--gold);color:var(--deep)}
.btn-bookmark.saved{background:var(--deep);color:var(--cream)}
.btn-bookmark:disabled{opacity:.6;cursor:wait}'''
            
            # Replace with regex - handle the full block
            new_content = re.sub(
                r'\.btn-bookmark\{[^}]+\}(\s*\.btn-bookmark:hover\{[^}]+\})?(\s*\.btn-bookmark\.saved\{[^}]+\})?(\s*\.btn-bookmark:disabled\{[^}]+\})?',
                new_style,
                content,
                count=1
            )
            if new_content != content:
                content = new_content
                changes.append('Fixed btn-bookmark color (minified)')
    else:
        # Pretty/formatted format (newer files like Agastya.html)
        pattern = r'\.btn-bookmark\s*\{[^}]+\}(\s*\.btn-bookmark:hover\s*\{[^}]+\})?(\s*\.btn-bookmark\.saved\s*\{[^}]+\})?(\s*\.btn-bookmark:disabled\s*\{[^}]+\})?'
        
        if '.btn-bookmark {' in content or '.btn-bookmark{' in content:
            new_style = '''    .btn-bookmark { display: inline-flex; align-items: center; gap: 8px; background: var(--forest); border: none; color: #fff; font-family: 'Jost', sans-serif; font-size: 10px; font-weight: 300; letter-spacing: 3px; text-transform: uppercase; padding: 10px 20px; cursor: pointer; border-radius: 0; transition: background 0.3s, color 0.3s; position: relative; z-index: 2; }
    .btn-bookmark:hover { background: var(--gold); color: var(--deep); }
    .btn-bookmark.saved { background: var(--deep); color: var(--cream); }
    .btn-bookmark:disabled { opacity: 0.6; cursor: wait; }'''
            
            new_content = re.sub(
                r'    \.btn-bookmark\s*\{[^}]+\}(\s*    \.btn-bookmark:hover\s*\{[^}]+\})?(\s*    \.btn-bookmark\.saved\s*\{[^}]+\})?(\s*    \.btn-bookmark:disabled\s*\{[^}]+\})?',
                new_style,
                content,
                count=1
            )
            if new_content != content:
                content = new_content
                changes.append('Fixed btn-bookmark color (pretty)')

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return changes
    return []

def fix_garden_file():
    """Fix the index.html filter checkbox and button color issues"""
    garden_path = os.path.join(AYUSH_DIR, 'index.html')
    with open(garden_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    original = content
    changes = []

    # ── FIX 1: Make filter checkboxes more visible ───────────────────────────
    # Current: border rgba(42,92,63,0.35), inner dot 6px green, bg rgba(42,92,63,0.07)
    # Fix: make active state much more visible
    
    old_check = '.filter-check { width: 14px; height: 14px; min-width: 14px; border: 1px solid rgba(42,92,63,0.35); position: relative; transition: border-color 0.3s, background 0.3s; }'
    new_check = '.filter-check { width: 14px; height: 14px; min-width: 14px; border: 1.5px solid rgba(42,92,63,0.35); position: relative; transition: border-color 0.3s, background 0.3s; }'
    
    old_check_after = ".filter-check::after { content: ''; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%) scale(0); width: 6px; height: 6px; background: var(--forest); transition: transform 0.25s cubic-bezier(0.34,1.56,0.64,1); }"
    new_check_after = ".filter-check::after { content: '✓'; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%) scale(0); font-size: 10px; line-height: 1; color: #fff; transition: transform 0.25s cubic-bezier(0.34,1.56,0.64,1); }"
    
    old_active_check = '.filter-option.active .filter-check { border-color: var(--forest); background: rgba(42,92,63,0.07); }'
    new_active_check = '.filter-option.active .filter-check { border-color: var(--forest); background: var(--forest); }'
    
    old_active_after = '.filter-option.active .filter-check::after { transform: translate(-50%,-50%) scale(1); }'
    new_active_after = '.filter-option.active .filter-check::after { transform: translate(-50%,-50%) scale(1); }'
    
    if old_check in content:
        content = content.replace(old_check, new_check)
        changes.append('Thickened filter checkbox border')
    
    if old_check_after in content:
        content = content.replace(old_check_after, new_check_after)
        changes.append('Changed filter checkbox inner to checkmark')
    
    if old_active_check in content:
        content = content.replace(old_active_check, new_active_check)
        changes.append('Made active filter checkbox fully green')
    
    # ── FIX 3: Make btn-bookmark in index.html green ────────────────────────
    old_btn = '.btn-bookmark { display: inline-flex; align-items: center; gap: 8px; background: none; border: 1px solid rgba(201,168,76,0.4); color: var(--gold); font-family: \'Jost\', sans-serif; font-size: 10px; font-weight: 300; letter-spacing: 3px; text-transform: uppercase; padding: 10px 20px; cursor: pointer; border-radius: 0; transition: background 0.3s, color 0.3s, border-color 0.3s; position: relative; z-index: 2; }'
    new_btn = ".btn-bookmark { display: inline-flex; align-items: center; gap: 8px; background: var(--forest); border: none; color: #fff; font-family: 'Jost', sans-serif; font-size: 10px; font-weight: 300; letter-spacing: 3px; text-transform: uppercase; padding: 10px 20px; cursor: pointer; border-radius: 0; transition: background 0.3s, color 0.3s; position: relative; z-index: 2; }"
    
    if old_btn in content:
        content = content.replace(old_btn, new_btn)
        changes.append('Fixed btn-bookmark color in index.html')
    
    old_btn_hover = '.btn-bookmark:hover { background: var(--gold); color: white; border-color: var(--gold); }'
    new_btn_hover = '.btn-bookmark:hover { background: var(--gold); color: var(--deep); }'
    
    if old_btn_hover in content:
        content = content.replace(old_btn_hover, new_btn_hover)
        changes.append('Fixed btn-bookmark hover in index.html')
    
    old_btn_saved = '.btn-bookmark.saved { background: var(--forest); color: var(--cream); border-color: var(--forest); }'
    new_btn_saved = '.btn-bookmark.saved { background: var(--deep); color: var(--cream); }'
    
    if old_btn_saved in content:
        content = content.replace(old_btn_saved, new_btn_saved)
        changes.append('Fixed btn-bookmark.saved in index.html')

    if content != original:
        with open(garden_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"index.html: {', '.join(changes)}")
    else:
        print("index.html: No changes made (patterns may differ)")
    
    return changes

print("=" * 60)
print("AYUSH Plant Pages - Fix Script")
print("=" * 60)

# Fix index.html
print("\n[1] Fixing index.html...")
garden_changes = fix_garden_file()

# Fix individual plant pages
print("\n[2] Fixing individual plant pages...")
plant_files = [
    f for f in os.listdir(AYUSH_DIR)
    if f.endswith('.html') and f not in SKIP_FILES
]
plant_files.sort()

total_fixed = 0
for filename in plant_files:
    filepath = os.path.join(AYUSH_DIR, filename)
    changes = fix_plant_file(filepath, filename)
    if changes:
        print(f"  ✓ {filename}: {', '.join(changes)}")
        total_fixed += 1

print(f"\n{'=' * 60}")
print(f"Done! Fixed {total_fixed} plant pages + index.html")
print(f"{'=' * 60}")
