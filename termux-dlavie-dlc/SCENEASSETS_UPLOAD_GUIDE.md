# 📦 Cara Upload Data FIFA 16 Baru (Sceneassets Terpisah)

## 🎯 Sistem Baru

```
SEBELUM:
dlavie26-data.zip (1.37 GB) → semua data + sceneassets dalam 1 file
  ↓ User download 1.37 GB sekali

SESUDAH:
dlavie26-data.zip (kecil) → data inti TANPA sceneassets
dlavie26-sceneassets.zip (besar) → sceneassets HD (OPTIONAL)
  ↓ User download data inti dulu (game bisa langsung main)
  ↓ User pilih download sceneassets kalau mau HD textures
```

## 📋 Langkah-Langkah

### Opsi A: Anda Punya Data FIFA 16 Baru (Folder)

**Step 1**: Jalankan script zip-split

```bash
# Di Termux atau laptop
python /home/z/my-project/scripts/split_sceneassets.py \
  --from-folder /sdcard/path/ke/data/fifa16 \
  --output-dir /sdcard/dlavie-dlc/splits
```

Output:
```
dlavie26-data-core.zip       (data inti, tanpa sceneassets)
dlavie26-sceneassets.zip     (sceneassets HD)
```

### Opsi B: Anda Punya dlavie26-data.zip Existing (Ingin Split)

```bash
python /home/z/my-project/scripts/split_sceneassets.py \
  /sdcard/Download/dlavie26-data.zip \
  --output-dir /sdcard/dlavie-dlc/splits
```

Script akan:
1. Baca zip existing
2. Pisahkan entry sceneassets → `dlavie26-sceneassets.zip`
3. Entry lainnya → `dlavie26-data-core.zip`
4. Hitung SHA-256 untuk kedua file

---

### Step 2: Upload ke Release v26

#### A. Upload `dlavie26-data-core.zip` (Replace yang lama)

```bash
# Pakai update_dlc.py (sudah ada di Termux)
# ATAU pakai script Python manual:

python << 'EOF'
import json, urllib.request, urllib.parse, os
from pathlib import Path

TOKEN = 'YOUR_GITHUB_TOKEN'
REPO = 'drmacze/DLavie-Launcher-Data'
RELEASE_ID = 346523648  # v26

# Get release info
url = f'https://api.github.com/repos/{REPO}/releases/{RELEASE_ID}'
req = urllib.request.Request(url, headers={'Authorization': f'token {TOKEN}'})
with urllib.request.urlopen(req) as r:
    release = json.loads(r.read())

# Hapus dlavie26-data.zip lama
for asset in release.get('assets', []):
    if asset['name'] == 'dlavie26-data.zip':
        del_url = f'https://api.github.com/repos/{REPO}/releases/assets/{asset["id"]}'
        urllib.request.urlopen(urllib.request.Request(del_url, method='DELETE', headers={'Authorization': f'token {TOKEN}'}))

# Upload file baru dengan nama 'dlavie26-data.zip' (tetap sama)
upload_url = release['upload_url'].split('{')[0]
zip_path = '/sdcard/dlavie-dlc/splits/dlavie26-data-core.zip'
with open(zip_path, 'rb') as f:
    zip_data = f.read()

url = f'{upload_url}?name=dlavie26-data.zip'
req = urllib.request.Request(
    url, data=zip_data, method='POST',
    headers={
        'Authorization': f'token {TOKEN}',
        'Content-Type': 'application/zip',
    }
)
with urllib.request.urlopen(req) as r:
    body = json.loads(r.read())
    print(f'✓ dlavie26-data.zip uploaded: {body["browser_download_url"]}')
    print(f'  Size: {body["size"]:,} bytes')
EOF
```

#### B. Upload `dlavie26-sceneassets.zip` (Asset Baru)

```bash
python << 'EOF'
import json, urllib.request, urllib.parse
from pathlib import Path

TOKEN = 'YOUR_GITHUB_TOKEN'
REPO = 'drmacze/DLavie-Launcher-Data'
RELEASE_ID = 346523648

# Get release info
url = f'https://api.github.com/repos/{REPO}/releases/{RELEASE_ID}'
req = urllib.request.Request(url, headers={'Authorization': f'token {TOKEN}'})
with urllib.request.urlopen(req) as r:
    release = json.loads(r.read())

# Hapus asset lama kalau ada
for asset in release.get('assets', []):
    if asset['name'] == 'dlavie26-sceneassets.zip':
        del_url = f'https://api.github.com/repos/{REPO}/releases/assets/{asset["id"]}'
        urllib.request.urlopen(urllib.request.Request(del_url, method='DELETE', headers={'Authorization': f'token {TOKEN}'}))

# Upload sceneassets
upload_url = release['upload_url'].split('{')[0]
zip_path = '/sdcard/dlavie-dlc/splits/dlavie26-sceneassets.zip'
with open(zip_path, 'rb') as f:
    zip_data = f.read()

url = f'{upload_url}?name=dlavie26-sceneassets.zip'
req = urllib.request.Request(
    url, data=zip_data, method='POST',
    headers={
        'Authorization': f'token {TOKEN}',
        'Content-Type': 'application/zip',
    }
)
with urllib.request.urlopen(req) as r:
    body = json.loads(r.read())
    print(f'✓ dlavie26-sceneassets.zip uploaded: {body["browser_download_url"]}')
    print(f'  Size: {body["size"]:,} bytes')
EOF
```

---

### Step 3: Update Manifest dengan Size + SHA-256 Baru

Jalankan script ini dengan size + SHA yang baru dihitung:

```bash
python << 'EOF'
import json, urllib.request, base64, hashlib
from pathlib import Path

TOKEN = 'YOUR_GITHUB_TOKEN'
REPO = 'drmacze/DLavie-Launcher-Data'
BRANCH = 'main'

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            chunk = f.read(8192)
            if not chunk: break
            h.update(chunk)
    return h.hexdigest()

# Hitung SHA-256 dan size file baru
core_zip = Path('/sdcard/dlavie-dlc/splits/dlavie26-data-core.zip')
scene_zip = Path('/sdcard/dlavie-dlc/splits/dlavie26-sceneassets.zip')

core_size = core_zip.stat().st_size
core_sha = sha256_file(core_zip)
scene_size = scene_zip.stat().st_size
scene_sha = sha256_file(scene_zip)

print(f'Core: {core_size:,} bytes, SHA: {core_sha}')
print(f'Scene: {scene_size:,} bytes, SHA: {scene_sha}')

# Fetch manifest
url = f'https://api.github.com/repos/{REPO}/contents/manifest.json?ref={BRANCH}'
req = urllib.request.Request(url, headers={'Authorization': f'token {TOKEN}'})
with urllib.request.urlopen(req) as r:
    body = json.loads(r.read())
existing_sha = body['sha']
manifest = json.loads(base64.b64decode(body['content']).decode())

# Update core_files (dlavie26-data.zip)
for f in manifest['game_data']['core_files']:
    if f['name'] == 'dlavie26-data.zip':
        f['size'] = core_size
        f['sha256'] = core_sha
        f['url'] = 'https://github.com/drmacze/DLavie-Launcher-Data/releases/download/v26/dlavie26-data.zip'
        f['note'] = 'Data inti FIFA 16 (TANPA sceneassets HD). Berisi: cl.ini, ai.ini, data/flows, data/ux, data/db, audio, dll.'

# Update optional_files (dlavie26-sceneassets.zip)
for f in manifest['game_data']['optional_files']:
    if f['name'] == 'dlavie26-sceneassets.zip':
        f['size'] = scene_size
        f['sha256'] = scene_sha
        f['url'] = 'https://github.com/drmacze/DLavie-Launcher-Data/releases/download/v26/dlavie26-sceneassets.zip'
        f['estimated_size_mb'] = scene_size // 1024 // 1024

# Upload manifest
content_b64 = base64.b64encode(json.dumps(manifest, indent=2).encode()).decode()
payload = {
    'message': 'feat(data): split sceneassets from core data\n\nCore data (without sceneassets): {} bytes\nSceneassets (optional): {} bytes'.format(core_size, scene_size),
    'content': content_b64,
    'branch': BRANCH,
    'sha': existing_sha,
}
url = f'https://api.github.com/repos/{REPO}/contents/manifest.json'
req = urllib.request.Request(
    url, data=json.dumps(payload).encode(), method='PUT',
    headers={
        'Authorization': f'token {TOKEN}',
        'Content-Type': 'application/json',
    }
)
with urllib.request.urlopen(req) as r:
    body = json.loads(r.read())
    print(f'✓ Manifest updated! Commit: {body["commit"]["sha"][:8]}')
EOF
```

---

### Step 4: Test di Launcher

Setelah upload + manifest update:

1. **Buka Launcher v7.9.43+** di HP
2. **Install game data inti** (DLavie26.apk + OBB + dlavie26-data.zip) — tanpa sceneassets
3. **Game bisa langsung dimainkan** (tanpa HD textures)
4. **Pilih download sceneassets** (optional):
   - Buka GameHub → tap "Download HD Sceneassets (Optional)"
   - Atau buka DLC tab → ada card "HD Sceneassets"
5. Launcher download sceneassets.zip → verify SHA → extract ke `data/sceneassets/`
6. Game langsung pakai HD textures tanpa restart

---

## 📊 Estimasi Size

| File | Estimasi Size | Required |
|------|---------------|----------|
| DLavie26.apk | 32 MB | ✅ Required |
| main.13.obb | 1.31 GB | ✅ Required |
| patch.26.obb | 98 MB | ✅ Required |
| dlavie26-data.zip (CORE) | ~800 MB (tanpa sceneassets) | ✅ Required |
| dlavie26-sceneassets.zip | ~500 MB | ❌ Optional |

**Total required download**: 2.24 GB (turun dari 2.74 GB sebelumnya)
**Dengan sceneassets**: 2.74 GB (sama seperti sebelumnya, tapi user pilih)

---

## 🎯 Keuntungan Sistem Baru

1. **User hemat kuota** — bisa skip sceneassets kalau kuota terbatas
2. **Game tetap jalan** tanpa sceneassets (cuma visual tidak HD)
3. **Download bertahap** — install core dulu, sceneassets nanti
4. **Update sceneassets terpisah** — kalau ada update HD texture, user download sceneassets.zip baru tanpa reinstall core

---

## ❓ FAQ

**Q: Bisakah user main game tanpa sceneassets?**
A: YA. Game tetap jalan, cuma texture tidak HD (mungkin blurry atau default texture).

**Q: Kalau user install sceneassets, lalu uninstall, apa game tetap jalan?**
A: YA. Cuma texture balik ke default (tidak HD).

**Q: Bagaimana update sceneassets ke versi baru?**
A: Upload sceneassets.zip baru ke release v26 (replace), update SHA di manifest. Launcher v7.9.43+ akan deteksi versi baru via marker file.

**Q: Apakah file sceneassets lama dihapus saat update?**
A: Tidak otomatis. User harus tap "Uninstall Sceneassets" dulu, lalu download yang baru. Atau Launcher detect SHA berbeda → auto-reinstall.
