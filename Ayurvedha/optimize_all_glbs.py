import struct
import json
import io
import os
import shutil
import glob
from PIL import Image

def optimize_glb(glb_path: str):
    print(f"\n--- Processing {glb_path} ---")
    backup_path = glb_path.replace('.glb', '_backup.glb')
    if not os.path.exists(backup_path):
        shutil.copyfile(glb_path, backup_path)
        print(f"  Backed up to {backup_path}")

    with open(glb_path, 'rb') as f:
        header = f.read(12)
        magic, version, total_len = struct.unpack('<4sII', header)
        if magic != b'glTF':
            print("  Not a valid glTF file, skipping.")
            return

        c0_len, c0_type = struct.unpack('<II', f.read(8))
        json_bytes = f.read(c0_len)
        gltf = json.loads(json_bytes.decode('utf-8'))

        c1_len, c1_type = struct.unpack('<II', f.read(8))
        bin_data = f.read(c1_len)

    images = gltf.get('images', [])
    if not images:
        print("  No embedded images found.")
        return

    bvs = gltf['bufferViews']
    img_bv_indices = {img['bufferView']: i for i, img in enumerate(images) if 'bufferView' in img}

    # Convert textures
    new_img_bytes = {}
    for bv_idx, img_idx in img_bv_indices.items():
        bv = bvs[bv_idx]
        offset = bv.get('byteOffset', 0)
        length = bv['byteLength']
        orig_img_bytes = bin_data[offset:offset+length]

        # Check if already JPEG
        mime = images[img_idx].get('mimeType', '')
        if mime == 'image/jpeg' and length < 2 * 1024 * 1024:
            print(f"  Image {img_idx} is already optimized JPEG ({length/1024:.1f} KB).")
            new_img_bytes[bv_idx] = orig_img_bytes
            continue

        try:
            im = Image.open(io.BytesIO(orig_img_bytes))
            im_rgb = im.convert('RGB')
            # Downscale if larger than 2048
            w, h = im_rgb.size
            if max(w, h) > 2048:
                scale = 2048 / max(w, h)
                im_rgb = im_rgb.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)

            out_buf = io.BytesIO()
            im_rgb.save(out_buf, format='JPEG', quality=85, optimize=True)
            compressed_data = out_buf.getvalue()
            print(f"  Image {img_idx} ({w}x{h}): {len(orig_img_bytes)/1024/1024:.2f}MB -> {len(compressed_data)/1024/1024:.2f}MB")
            new_img_bytes[bv_idx] = compressed_data
            images[img_idx]['mimeType'] = 'image/jpeg'
        except Exception as err:
            print(f"  Failed to compress image {img_idx}: {err}")
            new_img_bytes[bv_idx] = orig_img_bytes

    # Reconstruct bufferViews and binary chunk
    new_bin = bytearray()
    new_bvs = []
    for i, bv in enumerate(bvs):
        while len(new_bin) % 4 != 0:
            new_bin.append(0)
        offset = len(new_bin)

        if i in new_img_bytes:
            data = new_img_bytes[i]
        else:
            old_off = bv.get('byteOffset', 0)
            data = bin_data[old_off:old_off + bv['byteLength']]

        new_bin.extend(data)
        new_bv = dict(bv)
        new_bv['byteOffset'] = offset
        new_bv['byteLength'] = len(data)
        new_bvs.append(new_bv)

    while len(new_bin) % 4 != 0:
        new_bin.append(0)

    gltf['bufferViews'] = new_bvs
    gltf['buffers'][0]['byteLength'] = len(new_bin)

    new_json_bytes = json.dumps(gltf, separators=(',', ':')).encode('utf-8')
    while len(new_json_bytes) % 4 != 0:
        new_json_bytes += b' '

    new_c0_len = len(new_json_bytes)
    new_c1_len = len(new_bin)
    new_total_len = 12 + 8 + new_c0_len + 8 + new_c1_len

    with open(glb_path, 'wb') as f:
        f.write(struct.pack('<4sII', magic, version, new_total_len))
        f.write(struct.pack('<II', new_c0_len, 0x4E4F534A))
        f.write(new_json_bytes)
        f.write(struct.pack('<II', new_c1_len, 0x004E4942))
        f.write(new_bin)

    print(f"  Saved {glb_path}: {total_len/1024/1024:.2f}MB -> {new_total_len/1024/1024:.2f}MB (Saved {(total_len - new_total_len)/1024/1024:.2f}MB)")

if __name__ == '__main__':
    for path in sorted(glob.glob('Ayurvedha/*3d.glb')):
        if '_backup' not in path and '_opt' not in path:
            optimize_glb(path)

