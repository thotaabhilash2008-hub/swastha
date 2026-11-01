import os
import re
from gtts import gTTS
import glob

print("Starting batch process...")

# For all html files
for filepath in glob.glob("*.html"):
    filename = os.path.basename(filepath)
    if filename.lower() in ["amla.html", "index.html", "login.html", "bookmarks.html"]:
        continue
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # check if open3D exists
    if 'id="open3D"' not in content:
        continue

    # extract herb name
    match = re.search(r'<div class="hero-title">(.*?)</div>', content)
    if not match:
        match = re.search(r'<title>(.*?)</title>', content)
        if match:
            herb_name = match.group(1).split("—")[0].strip().split("|")[0].strip()
        else:
            herb_name = filename.replace('.html', '')
    else:
        herb_name = match.group(1).strip()
    
    audio_filename = f"{herb_name.lower().replace(' ', '_')}_benefits.mp3"
    audio_id = f"{herb_name.lower().replace(' ', '_')}Audio"
    
    print(f"Processing {filename}: {herb_name}")

    if audio_id in content:
        print(f"Skipping {filename}, already processed.")
        continue

    text_match = re.search(r'<p class="intro-text">(.*?)</p>', content, re.DOTALL)
    if text_match:
        text = text_match.group(1)
        text = re.sub(r'<[^>]+>', '', text)
        text = text.replace('\n', ' ').strip()
    else:
        text = f"{herb_name} is a powerful Ayurvedic herb known for its numerous health benefits."

    # Generate Audio
    if not os.path.exists(audio_filename):
        print(f"Generating audio for {herb_name}...")
        try:
            tts = gTTS(text=text, lang='en')
            tts.save(audio_filename)
        except Exception as e:
            print(f"Failed to generate audio for {herb_name}: {e}")
            continue

    # Inject Audio Tag
    audio_tag = f'\n<audio id="{audio_id}" src="{audio_filename}" loop preload="auto"></audio>\n'
    if '</body>' in content:
        content = content.replace('</body>', audio_tag + '</body>')
    else:
        content += audio_tag

    # Inject JS into openModal
    play_code = f"\n        var _aud = document.getElementById('{audio_id}'); if(_aud){{ _aud.currentTime=0; var playPromise = _aud.play(); if (playPromise !== undefined) {{ playPromise.catch(function(e){{ console.log(e); }}); }} }}\n"
    content = re.sub(r'(function\s+openModal\s*\([^)]*\)\s*\{)', r'\1' + play_code, content)

    # Inject JS into closeModal
    pause_code = f"\n        var _aud = document.getElementById('{audio_id}'); if(_aud){{ _aud.pause(); }}\n"
    content = re.sub(r'(function\s+closeModal\s*\([^)]*\)\s*\{)', r'\1' + pause_code, content)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
        
    print(f"Successfully updated {filename}")

print("Done.")
