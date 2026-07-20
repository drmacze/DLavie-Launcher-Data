# DLavie-Launcher-Data

> ⚠️ **README ini WAJIB dibaca oleh AI agent sebelum mengubah apa pun di repo ini.**
> Repo ini adalah **sumber kebenaran tunggal** untuk data launcher DLavie. Kesalahan di sini = break semua user.

Repository pusat data untuk DLavie Launcher. Berisi:
- `manifest.json` — Source of truth untuk versi launcher terbaru + game data files
- `banner_slides.json` — Banner slider yang tampil di beranda launcher
- `news_posts.json` — News posts yang tampil di beranda launcher
- Game data (APK + OBB) via GitHub Releases tag `v26`
- Launcher APKs (semua versi) via GitHub Releases tag `v26`

---

## 🚨 CRITICAL RULES FOR AI AGENTS

### 1. Jangan pernah ubah `manifest.json` tanpa reason jelas

`manifest.json` adalah **source of truth** untuk update system. Semua launcher user (ribuan device) membaca file ini setiap app dibuka.

**Yang boleh diubah**:
- `launcher.latest_version_code` — saat release APK baru
- `launcher.latest_version_name` — saat release APK baru
- `launcher.apk_url` — saat release APK baru
- `launcher.release_notes` — prepend entry baru (max 10 items)
- `updated_at` — timestamp terbaru

**Yang JANGAN diubah**:
- `schema_version` (tetap `3`)
- `manifest_url` (tetap URL raw file ini sendiri)
- `launcher.min_version_code` (tetap `206`)
- `game_data.*` (FIFA 16 game data tidak berubah)
- `mods.*` (mod patches managed via Dev Dashboard)

### 2. Jangan pernah ubah `game_data.core_files[].sha256`

SHA-256 hash digunakan untuk verifikasi integritas download. Jika hash salah, user download corrupt data. Hash sudah ditetapkan untuk:
- `DLavie26.apk`: `acb0ce50554d13d6d36aa75e7e84ade69e52f4b130f8316af4505cc255acd176`
- `main.13.com.ea.gp.fifaworld.obb`: `fe3e66c5e8c804656d8ee9ca62ace64a1fe968669f5c397b23ce174b0b8c720c`
- `patch.26.com.ea.gp.fifaworld.obb`: `bdca1604e7fc8dc80d96d656ae0e21ff3bd1ccf75a62ecaab0109dd269ef38a`
- `dlavie26-data.zip`: `4297a94017140497385a2ca1f6edade694c1e8e269e0751611e1bc29545bda85`

### 3. Jangan upload APK FIFA 16 baru

`DLavie26.apk` adalah APK ORIGINAL dari ChatGPT. Signature EA intact. **JANGAN repack** atau modify. Repack akan break signature → user can't install.

### 4. Workflow `auto-release.yml` di repo `F16-Launcher` otomatis update file ini

Saat push ke `main` di `F16-Launcher`:
1. Build APK baru
2. Sign dengan fixed keystore
3. Upload APK ke release `v26` di repo ini (asset name: `DLavie26-Launcher-v{versionCode}.apk`)
4. Update `manifest.json`:
   - `latest_version_code` → versionCode baru
   - `latest_version_name` → versionName baru
   - `apk_url` → URL APK baru
   - `release_notes` → prepend entry baru

**JANGAN** manual update `manifest.json` kecuali workflow gagal.

### 5. JSON files WAJIB valid array

`banner_slides.json` dan `news_posts.json` **HARUS** berupa JSON array (`[...]`), bukan object. Bukan string error. Bukan null.

**Cek sebelum commit**:
```bash
python3 -c "import json; data = json.load(open('banner_slides.json')); assert isinstance(data, list), 'Must be array'"
```

Pernah terjadi: file berisi pesan error Supabase `{"message":"Service for this project is restricted..."}` → NewsScreen gagal parse → beranda kosong.

---

## 📁 Struktur Repo

```
DLavie-Launcher-Data/
├── README.md              # This file
├── manifest.json          # Source of truth — version + game data spec
├── banner_slides.json     # Banner slider content (beranda launcher)
├── news_posts.json        # News posts content (beranda launcher)
└── termux-dlavie-dlc/     # (legacy, empty dir)
```

### GitHub Releases

- **Tag `v26`** (immutable): berisi APK + OBB FIFA 16 + semua versi Launcher APK
  - `DLavie26.apk` (34 MB) — FIFA 16 game APK
  - `main.13.com.ea.gp.fifaworld.obb` (1.4 GB) — OBB main
  - `patch.26.com.ea.gp.fifaworld.obb` (103 MB) — OBB patch
  - `dlavie26-data.zip` (1.4 GB) — Data inti FIFA 16
  - `dlavie26-sceneassets.zip` — Optional HD scene assets
  - `DLavie26-Launcher-v{N}.apk` (28 MB) — Launcher APK per version (v277-v324+)

---

## 📋 Schema: `manifest.json`

```json
{
  "schema_version": 3,
  "manifest_url": "https://raw.githubusercontent.com/drmacze/DLavie-Launcher-Data/main/manifest.json",
  "updated_at": "2026-07-20T01:31:24Z",
  "launcher": {
    "min_version_code": 206,
    "latest_version_code": 324,
    "latest_version_name": "8.0.26-fix-news-beranda",
    "apk_url": "https://github.com/drmacze/DLavie-Launcher-Data/releases/download/v26/DLavie26-Launcher-v324.apk",
    "release_notes": [
      "v8.0.26-fix-news-beranda: ...",
      "..."
    ]
  },
  "game_data": {
    "version": "v26",
    "package": "com.ea.gp.fifaworld",
    "target_activity": "com.ea.gp.fifaworld.fifa",
    "core_files": [
      {
        "type": "apk",
        "name": "DLavie26.apk",
        "url": "https://github.com/drmacze/DLavie-Launcher-Data/releases/download/v26/DLavie26.apk",
        "size": 34027637,
        "sha256": "acb0ce50554d13d6d36aa75e7e84ade69e52f4b130f8316af4505cc255acd176",
        "required": true,
        "note": "APK ORIGINAL dari ChatGpt. TIDAK dimodify. Signature intact."
      },
      {
        "type": "obb",
        "name": "main.13.com.ea.gp.fifaworld.obb",
        "url": "...",
        "size": 1376082760,
        "sha256": "fe3e66c5e8c804656d8ee9ca62ace64a1fe968669f5c397b23ce174b0b8c720c",
        "obb_target_path": "Android/obb/com.ea.gp.fifaworld/",
        "required": true
      },
      {
        "type": "obb",
        "name": "patch.26.com.ea.gp.fifaworld.obb",
        "url": "...",
        "size": 102869675,
        "sha256": "bdca1604e7fc8dc80d96d656ae0e21ff3bd1ccf75a62ecaab0109dd269ef38a",
        "obb_target_path": "Android/obb/com.ea.gp.fifaworld/",
        "required": true
      },
      {
        "type": "data_zip",
        "name": "dlavie26-data.zip",
        "url": "...",
        "size": 1440341039,
        "sha256": "4297a94017140497385a2ca1f6edade694c1e8e269e0751611e1bc29545bda85",
        "extract_to": "Android/data/com.ea.gp.fifaworld/",
        "required": true
      }
    ],
    "optional_files": [...]
  },
  "mods": [...]
}
```

### Field reference

| Path | Type | Description |
|------|------|-------------|
| `schema_version` | int | Tetap `3`. Jangan ubah. |
| `manifest_url` | string | URL raw file ini sendiri. Jangan ubah. |
| `updated_at` | string | ISO 8601 timestamp. Update setiap kali file berubah. |
| `launcher.min_version_code` | int | Versi minimum yang masih didukung (206). |
| `launcher.latest_version_code` | int | VersionCode APK terbaru. |
| `launcher.latest_version_name` | string | VersionName APK terbaru. |
| `launcher.apk_url` | string | URL download APK terbaru. |
| `launcher.release_notes` | string[] | Max 10 entry terbaru. Prepend baru di index 0. |
| `game_data.version` | string | Tetap `v26`. |
| `game_data.package` | string | Tetap `com.ea.gp.fifaworld`. |
| `game_data.target_activity` | string | Tetap `com.ea.gp.fifaworld.fifa`. |
| `game_data.core_files[].sha256` | string | **JANGAN UBAH** — verifikasi integritas. |

---

## 📋 Schema: `banner_slides.json`

```json
[
  {
    "id": 1,
    "sort_order": 1,
    "title": "DLavie Launcher",
    "subtitle": "Pengalaman modding FIFA 16 yang lebih cepat dan stabil",
    "media_type": "image",
    "media_url": "https://drmacze.github.io/dlavie-web/",
    "link_url": "https://drmacze.github.io/dlavie-web/",
    "duration_seconds": 5,
    "starts_at": "2026-07-20T00:00:00Z",
    "ends_at": "2026-12-31T23:59:59Z",
    "is_active": true
  }
]
```

### Aturan konten banner (WAJIB)

- ❌ **JANGAN** sebut "bug", "fix", "error", "quota exceeded"
- ❌ **JANGAN** sebut "Update Wajib" (terlalu aggressive)
- ❌ **JANGAN** sebut nomor versi spesifik (v324, dll)
- ✅ Bahasa Indonesia, professional, user-facing
- ✅ Maksimal 5 slides (lebih dari itu akan slow carousel)
- ✅ `sort_order` dimulai dari 1, increment
- ✅ `media_type` hanya support `image` saat ini (GIF/MP4 belum diimplement)

---

## 📋 Schema: `news_posts.json`

```json
[
  {
    "id": 1,
    "title": "DLavie Launcher v8.0 Telah Dirilis",
    "body": "Kami dengan bangga mengumumkan rilis DLavie Launcher v8.0...\n\nVersi ini membawa...",
    "footer_text": "Tim DLavie",
    "image_url": "",
    "label_type": "info",
    "official": true,
    "scheduled_at": null,
    "published_at": "2026-07-20T10:00:00Z",
    "created_at": "2026-07-20T10:00:00Z",
    "is_active": true
  }
]
```

### Field reference

| Path | Type | Description |
|------|------|-------------|
| `id` | int | Unique, increment. |
| `title` | string | Max 80 char. Professional, no jargon. |
| `body` | string | Markdown-style. Gunakan `\n\n` untuk paragraph break. |
| `footer_text` | string | Biasanya "Tim DLavie". |
| `image_url` | string | URL gambar (boleh kosong `""`). |
| `label_type` | string | `info` / `critical` / `warning` / `success`. |
| `official` | bool | `true` untuk announcement resmi. |
| `scheduled_at` | string\|null | ISO 8601 atau `null` (langsung publish). |
| `published_at` | string | ISO 8601 timestamp publish. |
| `created_at` | string | ISO 8601 timestamp create. |
| `is_active` | bool | `true` untuk tampil di beranda. |

### Aturan konten news (WAJIB)

- ❌ **JANGAN** sebut technical jargon: "bug", "fix", "quota exceeded", "Supabase", "JSON parse error"
- ❌ **JANGAN** sebut nomor versi spesifik di title (kecuali major release seperti "v8.0")
- ❌ **JANGAN** sebut "Update Wajib" di news (terlalu aggressive)
- ✅ Tulis professional, user-facing, fokus benefit
- ✅ Bahasa Indonesia (default)
- ✅ Signed "Tim DLavie"
- ✅ Maksimal 5 posts aktif

---

## 🔄 Update Process

### Otomatis (via workflow `F16-Launcher/auto-release.yml`)

Saat push ke `main` di `F16-Launcher`:
1. Build APK + sign
2. Upload APK ke release `v26` (asset: `DLavie26-Launcher-v{versionCode}.apk`)
3. Update `manifest.json`:
   - `latest_version_code` → versionCode baru
   - `latest_version_name` → versionName baru
   - `apk_url` → URL APK baru
   - `release_notes` → prepend entry baru

### Manual (jika workflow gagal)

Lihat script `/home/z/my-project/scripts/upload_v324_final.py` sebagai template:
```python
# 1. Download APK dari F16-Launcher release
# 2. Upload ke DLavie-Launcher-Data v26 release
# 3. Fetch manifest.json (dapat SHA)
# 4. Modify latest_version_code, latest_version_name, apk_url
# 5. PUT via GitHub API dengan SHA
```

### Update `banner_slides.json` / `news_posts.json` manual

Lihat `/home/z/my-project/scripts/fix_news_content_professional.py`:
```python
# 1. Fetch current JSON (dapat SHA)
# 2. Replace dengan array baru
# 3. PUT via GitHub API
```

---

## 🌐 URLs (konsisten lintas repo)

| Resource | URL |
|----------|-----|
| Repo | `https://github.com/drmacze/DLavie-Launcher-Data` |
| Manifest (raw) | `https://raw.githubusercontent.com/drmacze/DLavie-Launcher-Data/main/manifest.json` |
| Manifest (jsdelivr CDN) | `https://cdn.jsdelivr.net/gh/drmacze/DLavie-Launcher-Data@main/manifest.json` |
| Banner slides (raw) | `https://raw.githubusercontent.com/drmacze/DLavie-Launcher-Data/main/banner_slides.json` |
| Banner slides (jsdelivr) | `https://cdn.jsdelivr.net/gh/drmacze/DLavie-Launcher-Data@main/banner_slides.json` |
| News posts (raw) | `https://raw.githubusercontent.com/drmacze/DLavie-Launcher-Data/main/news_posts.json` |
| News posts (jsdelivr) | `https://cdn.jsdelivr.net/gh/drmacze/DLavie-Launcher-Data@main/news_posts.json` |
| Game APK | `https://github.com/drmacze/DLavie-Launcher-Data/releases/download/v26/DLavie26.apk` |
| Game OBB Main | `https://github.com/drmacze/DLavie-Launcher-Data/releases/download/v26/main.13.com.ea.gp.fifaworld.obb` |
| Game OBB Patch | `https://github.com/drmacze/DLavie-Launcher-Data/releases/download/v26/patch.26.com.ea.gp.fifaworld.obb` |
| Game Data ZIP | `https://github.com/drmacze/DLavie-Launcher-Data/releases/download/v26/dlavie26-data.zip` |
| Launcher APK v{N} | `https://github.com/drmacze/DLavie-Launcher-Data/releases/download/v26/DLavie26-Launcher-v{N}.apk` |

### CDN behavior

- **raw.githubusercontent.com**: Cache ~5 menit. Pakai `?t=timestamp` untuk cache-bust.
- **cdn.jsdelivr.net**: Cache ~10 menit. Refresh otomatis setelah git push.
- **api.github.com/repos/.../contents/**: Always fresh (no CDN cache). Base64-encoded content.

---

## 🐛 Troubleshooting

### News tidak muncul di launcher beranda

**Cek**:
1. `banner_slides.json` / `news_posts.json` valid JSON array (bukan error Supabase).
2. Verifikasi via API:
   ```bash
   curl -s -H "Authorization: token <PAT>"      https://api.github.com/repos/drmacze/DLavie-Launcher-Data/contents/banner_slides.json | \
     python3 -c "import json,sys,base64; print(base64.b64decode(json.load(sys.stdin)['content']).decode()[:200])"
   ```
3. Jika korup (berisi pesan error Supabase), replace dengan valid JSON.

### Update popup tidak muncul

**Cek** `manifest.json`:
- `launcher.latest_version_code` > user's `BuildConfig.VERSION_CODE`
- `launcher.apk_url` tidak kosong, format URL valid

### Workflow gagal update manifest

1. Cek workflow logs di `F16-Launcher/actions`
2. Jika step "Update manifest.json" gagal, manual update via API:
   ```bash
   curl -X PUT -H "Authorization: token <PAT>" \
     -d '{"message":"manual update","content":"<base64>","sha":"<sha>","branch":"main"}' \
     https://api.github.com/repos/drmacze/DLavie-Launcher-Data/contents/manifest.json
   ```

---

## ❓ Pertanyaan yang sering muncul di AI agent

**Q: Boleh tambah field baru ke manifest.json?**
A: Boleh, tapi jangan hapus field yang sudah ada. Tambah di akhir object. Update parser di `AppUpdateChecker.kt` + `ManifestApi.kt` di repo `F16-Launcher`.

**Q: Boleh ubah `game_data.version` dari `v26`?**
A: TIDAK. `v26` sudah fix, merepresentasikan season 2026 FIFA 16. Jika ingin update game data, upload file baru dengan nama beda (misal `dlavie27-data.zip`) dan tambah ke `core_files`.

**Q: Boleh hapus release tag `v26`?**
A: TIDAK PERNAH. Ribuan user download dari tag ini. Hapus = break semua install.

**Q: Cara rollback ke versi launcher lama?**
A: Edit `manifest.json` `latest_version_code` ke versi lama + `apk_url` ke APK lama. Tapi **TIDAK DISARANKAN** — buat versi baru dengan fix daripada rollback.

**Q: Boleh pakai Supabase untuk simpan data?**
A: TIDAK untuk data publik. Supabase sudah exceed egress quota. Pakai GitHub raw saja.

**Q: Berapa ukuran maksimum file di GitHub Release?**
A: 2 GB per file. `main.13.com.ea.gp.fifaworld.obb` (1.4 GB) masih aman.

**Q: Cara test manifest setelah update?**
A: Buka URL raw di browser, pastikan JSON valid: `https://raw.githubusercontent.com/drmacze/DLavie-Launcher-Data/main/manifest.json`

---

## 📚 Related Repos

| Repo | Purpose |
|------|---------|
| `F16-Launcher` | Android launcher app (Kotlin) — consumer of this data |
| `dlavie-web` | Website (HTML) — consumer of manifest for version display |
| `DLavie-Dev-Dashboard` | Admin dashboard — manage mods + patches |
| `DLavie-Patches` | FIFA 16 mod patches repo |

---

**Terakhir diperbarui**: 2026-07-20 (v324 launcher)
