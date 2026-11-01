#!/usr/bin/env python3
"""Add and update synchronized View in 3D button + modal across plant pages."""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DIR = Path(__file__).resolve().parent
SKIP = {
    "garden_backup.html",
    "login.html",
    "bookmarks.html",
    "index.html",
}

MV_SCRIPT = (
    '<script type="module" '
    'src="https://unpkg.com/@google/model-viewer/dist/model-viewer.min.js"></script>'
)

CSS_BLOCK = """
    #open3D {
      position: fixed;
      top: 25px;
      right: 30px;
      padding: 10px 20px;
      font-size: 11px;
      letter-spacing: 2px;
      text-transform: uppercase;
      background: linear-gradient(135deg, #103B28, #184c34);
      color: #F5F0E4;
      border: 1px solid rgba(200, 164, 93, 0.4);
      border-radius: 999px;
      cursor: pointer;
      z-index: 1000;
      box-shadow: 0 6px 20px rgba(0,0,0,0.4);
      transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
      display: inline-flex;
      align-items: center;
      gap: 8px;
    }
    #open3D:hover {
      background: linear-gradient(135deg, #C8A45D, #E5C783);
      color: #07170F;
      border-color: #E5C783;
      transform: translateY(-2px);
      box-shadow: 0 10px 25px rgba(200, 164, 93, 0.35);
    }
    #viewerModal {
      position: fixed !important;
      inset: 0 !important;
      width: 100vw !important;
      height: 100vh !important;
      z-index: 999999 !important;
      display: none;
      flex-direction: column;
      background: #07170F !important;
      background-color: #07170F !important;
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      overflow: hidden !important;
    }
    #viewerModal.is-open {
      display: flex !important;
    }
    #modal-topbar {
      flex-shrink: 0;
      height: 60px;
      background: #07170F;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 24px;
      border-bottom: 1px solid rgba(200, 164, 93, 0.25);
      z-index: 1000000;
    }
    #modal-topbar span {
      font-family: 'Cormorant Garamond', Georgia, serif;
      font-size: 15px;
      font-weight: 500;
      letter-spacing: 2px;
      text-transform: uppercase;
      color: #E5C783;
      user-select: none;
    }
    #close3D {
      width: 38px;
      height: 38px;
      background: rgba(255, 255, 255, 0.08);
      color: #F5F0E4;
      border: 1px solid rgba(200, 164, 93, 0.4);
      border-radius: 50%;
      cursor: pointer;
      z-index: 1000000;
      display: flex;
      align-items: center;
      justify-content: center;
      line-height: 1;
      font-size: 16px;
      font-weight: 300;
      transition: all 0.25s ease;
      outline: none;
      flex-shrink: 0;
    }
    #close3D:hover {
      background: #C8A45D;
      color: #07170F;
      border-color: #E5C783;
      transform: rotate(90deg);
    }
    .modal-viewer-wrap {
      flex: 1;
      width: 100%;
      height: calc(100% - 60px);
      position: relative;
      background: #07170F !important;
      display: flex;
      align-items: center;
      justify-content: center;
      overflow: hidden;
    }
    #viewerModal model-viewer,
    .modal-viewer-wrap model-viewer,
    model-viewer#plantModelViewer {
      width: 100% !important;
      height: 100% !important;
      display: block !important;
      background: #07170F !important;
      background-color: #07170F !important;
      --poster-color: transparent !important;
    }
    .model-loading-overlay {
      position: absolute;
      inset: 0;
      background: rgba(7, 23, 15, 0.92);
      backdrop-filter: blur(8px);
      -webkit-backdrop-filter: blur(8px);
      z-index: 40;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: opacity 0.4s ease, visibility 0.4s ease;
      pointer-events: none;
    }
    .model-loading-overlay.is-hidden {
      opacity: 0;
      visibility: hidden;
    }
    .model-loading-card {
      text-align: center;
      padding: 24px 28px;
      background: rgba(16, 59, 40, 0.85);
      border: 1px solid rgba(200, 164, 93, 0.35);
      border-radius: 16px;
      box-shadow: 0 20px 45px rgba(0, 0, 0, 0.7);
      max-width: 340px;
      width: 88%;
    }
    .model-loading-spinner {
      font-size: 26px;
      color: #E5C783;
      display: inline-block;
      animation: pulseRotate 2s infinite linear;
      margin-bottom: 10px;
    }
    @keyframes pulseRotate {
      0% { transform: rotate(0deg) scale(0.9); opacity: 0.7; }
      50% { transform: rotate(180deg) scale(1.15); opacity: 1; }
      100% { transform: rotate(360deg) scale(0.9); opacity: 0.7; }
    }
    .model-loading-title {
      font-family: 'Cormorant Garamond', Georgia, serif;
      font-size: 20px;
      font-weight: 500;
      color: #E5C783;
      letter-spacing: 1px;
      margin-bottom: 4px;
    }
    .model-loading-sub {
      font-size: 11px;
      color: #C7C9B9;
      letter-spacing: 1.5px;
      text-transform: uppercase;
      margin-bottom: 14px;
    }
    .model-progress-bar-wrap {
      width: 100%;
      height: 5px;
      background: rgba(255, 255, 255, 0.08);
      border-radius: 999px;
      overflow: hidden;
      border: 1px solid rgba(200, 164, 93, 0.2);
    }
    .model-progress-bar {
      width: 15%;
      height: 100%;
      background: linear-gradient(90deg, #C8A45D, #E5C783);
      border-radius: 999px;
      transition: width 0.25s ease;
    }
    @media (max-width: 768px) {
      #modal-topbar {
        padding: 0 14px;
        height: 52px;
      }
      #modal-topbar span {
        font-size: 11.5px;
        letter-spacing: 1px;
      }
      .modal-viewer-wrap {
        height: calc(100% - 52px);
      }
      .modal-audio-btn {
        padding: 4px 8px;
        font-size: 10px;
      }
    }
"""


def plant_title(html: str, filename: str) -> str:
    m = re.search(r'class="hero-title"[^>]*>(.*?)</', html, re.S | re.I)
    if m:
        return re.sub(r"<[^>]+>", "", m.group(1)).strip()
    m = re.search(r"<title>(.*?)</title>", html, re.I)
    if m:
        return m.group(1).split("—")[0].split("|")[0].strip()
    return Path(filename).stem.split("_")[0].strip()


def slug(title: str) -> str:
    s = title.lower()
    s = re.sub(r"[^a-z0-9]+", "", s)
    return s or "plant"


def audio_id(html: str) -> str | None:
    m = re.search(r'<audio[^>]+id="([^"]+)"', html, re.I)
    return m.group(1) if m else None


def inject_head_script(html: str, glb: str) -> str:
    preload_tag = f'<link rel="preload" href="{glb}" as="fetch" crossorigin="anonymous">\n'
    if "model-viewer.min.js" in html:
        if f'href="{glb}"' not in html:
            html = re.sub(r"(<script[^>]+model-viewer[^>]*></script>)", preload_tag + r"\1", html, count=1, flags=re.I)
        return html
    if re.search(r"</head>", html, re.I):
        return re.sub(r"</head>", f"  {preload_tag}  {MV_SCRIPT}\n</head>", html, count=1, flags=re.I)
    return html


def inject_css(html: str) -> str:
    if re.search(r"#open3D\s*\{", html):
        # Update existing CSS block if present
        return re.sub(r"#open3D\s*\{.*?\.modal-viewer-wrap\s*model-viewer\s*\{[^}]*\}", CSS_BLOCK.strip(), html, flags=re.S)
    return re.sub(r"(<style[^>]*>)", r"\1" + CSS_BLOCK, html, count=1, flags=re.I)


def inject_button_and_modal(html: str, title: str, glb: str, aud: str | None) -> str:
    if 'id="open3D"' not in html:
        html = re.sub(
            r"(<body[^>]*>)",
            r'\1\n  <button type="button" id="open3D">View in 3D</button>\n',
            html,
            count=1,
            flags=re.I,
        )

    # Build modal HTML
    audio_sync_logic = f"""
      var _aud = {f"document.getElementById('{aud}')" if aud else "null"};
      var isModelLoaded = false;

      function playAudioIfOpen() {{
        if (_aud && (modal.classList.contains('is-open') || modal.style.display === 'flex')) {{
          _aud.currentTime = 0;
          var p = _aud.play();
          if (p !== undefined) {{ p.catch(function(e) {{ console.log('Audio autoplay prevented:', e); }}); }}
        }}
      }}

      function onModelLoaded() {{
        isModelLoaded = true;
        if (badge) badge.classList.add('is-hidden');
        if (pBar) pBar.style.width = '100%';
        playAudioIfOpen();
      }}

      if (viewer) {{
        if (viewer.loaded) {{
          isModelLoaded = true;
          if (badge) badge.classList.add('is-hidden');
        }} else {{
          viewer.addEventListener('load', onModelLoaded);
          viewer.addEventListener('progress', function(evt) {{
            if (evt.detail && evt.detail.totalProgress !== undefined) {{
              var pct = Math.round(evt.detail.totalProgress * 100);
              if (pBar) pBar.style.width = Math.max(15, pct) + '%';
            }}
          }});
        }}
      }}

      function openModal() {{
        modal.classList.add('is-open');
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';

        if (isModelLoaded || (viewer && viewer.loaded)) {{
          if (badge) badge.classList.add('is-hidden');
          playAudioIfOpen();
        }} else {{
          if (_aud) {{ _aud.pause(); _aud.currentTime = 0; }}
          if (badge) badge.classList.remove('is-hidden');
        }}
      }}

      function closeModal() {{
        modal.classList.remove('is-open');
        modal.style.display = 'none';
        document.body.style.overflow = '';
        if (_aud) {{
          _aud.pause();
          _aud.currentTime = 0;
        }}
      }}
"""

    modal = f"""
  <div id="viewerModal">
    <div id="modal-topbar">
      <span>3D Botanical Specimen — {title}</span>
      <button type="button" id="close3D" title="Close 3D View">✕</button>
    </div>
    <div class="modal-viewer-wrap">
      <div id="modelLoadingBadge" class="model-loading-overlay">
        <div class="model-loading-card">
          <div class="model-loading-spinner">✦</div>
          <div class="model-loading-title">Materializing 3D {title}</div>
          <div class="model-loading-sub">Loading geometry &amp; textures...</div>
          <div class="model-progress-bar-wrap">
            <div id="modelProgressBar" class="model-progress-bar"></div>
          </div>
        </div>
      </div>
      <model-viewer id="plantModelViewer" src="{glb}" loading="eager" reveal="auto" auto-rotate camera-controls shadow-intensity="1" exposure="1"></model-viewer>
    </div>
  </div>
  <script>
    (function() {{
      var open3D = document.getElementById('open3D');
      var close3D = document.getElementById('close3D');
      var modal = document.getElementById('viewerModal');
      var viewer = document.getElementById('plantModelViewer');
      var badge = document.getElementById('modelLoadingBadge');
      var pBar = document.getElementById('modelProgressBar');
      if (!open3D || !close3D || !modal) return;
{audio_sync_logic}
      open3D.addEventListener('click', function (e) {{
        e.preventDefault(); e.stopPropagation(); openModal();
      }});
      close3D.addEventListener('click', function (e) {{
        e.preventDefault(); e.stopPropagation(); closeModal();
      }});
      modal.addEventListener('click', function(e) {{
        if (e.target === modal) closeModal();
      }});
      document.addEventListener('keydown', function (e) {{
        if (e.key === 'Escape' && (modal.classList.contains('is-open') || modal.style.display === 'flex')) closeModal();
      }});
    }})();
  </script>
"""

    # If viewerModal already exists in the file, replace it
    if 'id="viewerModal"' in html:
        html = re.sub(r'<div id="viewerModal">.*?<\/script>', modal.strip(), html, flags=re.S)
    else:
        html = re.sub(r"</body>", modal + "\n</body>", html, count=1, flags=re.I)

    return html


def update_target_pages() -> None:
    # Update known pages that have 3D models and audio
    key_models = {
        "Tulsi.html": ("Tulsi", "tulsi3d.glb", "tulsiAudio"),
        "Tulasi _ Holy Basil.html": ("Tulasi", "tulsi3d.glb", "tulsiAudio"),
        "ashwagandha.html": ("Ashwagandha", "ashwagandha3d.glb", "ashwagandhaAudio"),
        "amla.html": ("Amla", "amla3d.glb", "amlaAudio"),
        "bhringraj.html": ("Bhringraj", "bhringraj3d.glb", "bhringrajAudio"),
        "brahmi.html": ("Brahmi", "brahmi3d.glb", "brahmiAudio"),
        "neem.html": ("Neem", "neem3d.glb", "tulsiAudio"),
        "Nimba  Neem.html": ("Neem", "neem3d.glb", "tulsiAudio"),
    }

    for fname, (title, glb, aud) in key_models.items():
        p = DIR / fname
        if p.exists():
            html = p.read_text(encoding="utf-8", errors="replace")
            # detect actual audio id if present
            actual_aud = audio_id(html) or aud
            html = inject_head_script(html, glb)
            html = inject_css(html)
            html = inject_button_and_modal(html, title, glb, actual_aud)
            p.write_text(html, encoding="utf-8")
            print(f"Synchronized & optimized 3D audio modal for: {fname} ({glb}, audio: {actual_aud})")


if __name__ == "__main__":
    update_target_pages()
