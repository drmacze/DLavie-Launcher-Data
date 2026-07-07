# 📱 DLavie DLC Manager — Termux Edition

Kelola DLC mod FIFA 16 langsung dari HP Android Anda, tanpa laptop.

## 🚀 Quick Start (5 menit)

### Step 1: Install Termux
1. Download Termux dari F-Droid: https://f-droid.org/packages/com.termux/
   - ⚠️ **JANGAN** dari Play Store (versi lama, tidak update)
2. Buka Termux, ketik:
   ```bash
   pkg update -y && pkg install git curl -y
   ```

### Step 2: Jalankan Installer
Copy-paste command ini ke Termux (1 baris):

```bash
curl -sL https://raw.githubusercontent.com/drmacze/DLavie-Launcher-Data/main/termux-dlavie-dlc/setup/install.sh | bash
```

Installer akan:
- Install Python, git, curl
- Buat folder kerja di `/sdcard/dlavie-dlc/`
- Download script `update_dlc.py`
- Setup GitHub token (minta Anda paste token)
- Buat command `dlavie-dlc` yang bisa dipanggil dari mana saja

### Step 3: Dapatkan GitHub Token
1. Buka https://github.com/settings/tokens di browser HP
2. Login akun GitHub (drmacze)
3. Klik **"Generate new token (classic)"**
4. Set:
   - **Note**: `dlavie-dlc-termux`
   - **Expiration**: 90 days (atau No expiration)
   - **Scopes**: centang `repo` (full control of private repositories)
5. Klik **Generate token** di bawah
6. **Copy token** (format: `ghp_xxxxxxxxxxxxxxxxxxxx`)

Paste ke Termux saat installer minta.

## 📦 Cara Pakai

### Bikin Mod Baru
```bash
dlavie-dlc new DLC_MyFeature
```
Akan dibuat folder `/sdcard/dlavie-dlc/mods/DLC_MyFeature/` dengan template.

Edit file di folder itu pakai file manager Android (misal MiXplorer, Solid Explorer) atau text editor seperti QuickEdit.

### Upload Mod ke Server
```bash
dlavie-dlc upload DLC_MyFeature 1.0.0 --note "Initial release"
```

Script akan otomatis:
1. Package folder jadi ZIP
2. Upload ZIP ke release v26 di GitHub
3. Update manifest.json (auto-commit)
4. Launcher user akan auto-detect versi baru dalam 15 menit

### Lihat Semua Mod
```bash
dlavie-dlc list
```

### Hapus Versi Tertentu
```bash
dlavie-dlc delete my-feature 1.0.0
```

### Upload Versi Baru (Update)
Edit file di folder mod, lalu:
```bash
dlavie-dlc upload DLC_MyFeature 1.0.1 --note "Fix bug XYZ"
```

## 📁 Struktur Folder Kerja

```
/sdcard/dlavie-dlc/
├── bin/
│   └── update_dlc.py         ← script utama (jangan edit)
├── mods/                      ← FOLDER KERJA ANDA
│   ├── DLC_SaveMenuEnhancer/  ← contoh mod existing
│   │   ├── cl.ini
│   │   ├── data/
│   │   │   └── flows/...
│   │   └── README.md
│   └── DLC_NewMod/            ← mod baru yang Anda bikin
│       ├── cl.ini
│       └── data/...
└── template/                  ← template contoh
    └── example_mod/
        ├── cl.ini
        └── README.md
```

## 🎯 Workflow Lengkap (Contoh Nyata)

### Skenario: Fix bug di Save Menu Enhancer

1. **Clone mod existing** (sekali saja):
   ```bash
   cd /sdcard/dlavie-dlc/mods
   git clone https://github.com/drmacze/F16.git --depth 1 f16-temp
   mkdir -p DLC_SaveMenuEnhancer
   cp f16-temp/cl.ini DLC_SaveMenuEnhancer/
   cp -r f16-temp/data/flows/mainflow/gamemodes/MainMenu/Customize DLC_SaveMenuEnhancer/data/flows/mainflow/gamemodes/MainMenu/
   rm -rf f16-temp
   ```

2. **Edit file** (pakai file manager Android):
   - Buka `/sdcard/dlavie-dlc/mods/DLC_SaveMenuEnhancer/`
   - Edit `cl.ini` atau `SaveHub.lua` sesuai kebutuhan

3. **Upload versi baru**:
   ```bash
   dlavie-dlc upload DLC_SaveMenuEnhancer 1.0.1 --note "Fix crash on Android 11"
   ```

4. **Verifikasi**:
   ```bash
   dlavie-dlc list
   ```
   Output:
   ```
   [save-menu-enhancer]
     Latest: v1.0.1
     Published: True
     Versions: 2
       - v1.0.1 (21050 bytes, 2026-07-07)
       - v1.0.0 (20911 bytes, 2026-07-07)
   ```

5. **User otomatis dapat update** dalam 15 menit (Launcher auto-fetch manifest)

## 🔧 Troubleshooting

### Error: "GITHUB_TOKEN not set"
```bash
echo "export GITHUB_TOKEN=ghp_xxxxxxxx" >> ~/.bashrc
source ~/.bashrc
```

### Error: "Permission denied" saat akses /sdcard
Jalankan:
```bash
termux-setup-storage
```
Lalu buka Settings Android → Apps → Termux → Permissions → Storage → Allow.

### Error: "ModuleNotFoundError: No module named 'urllib3'"
```bash
pip install urllib3
```

### Command `dlavie-dlc` tidak ditemukan
```bash
export PATH="$PATH:/data/data/com.termux/files/usr/bin"
```
Atau reopen Termux.

### Download ZIP gagal dari HP
Cek koneksi internet. Kalau pakai data seluler, pastikan sinyal kuat. GitHub kadang lambat di Indonesia, coba lagi 1-2 menit.

## 📋 Command Reference

| Command | Fungsi |
|---------|--------|
| `dlavie-dlc upload <folder> <ver> [--note '...']` | Upload DLC baru |
| `dlavie-dlc upload <folder> <ver> --critical` | Upload sebagai critical update |
| `dlavie-dlc upload <folder> <ver> --title 'Custom Title'` | Upload dengan title custom |
| `dlavie-dlc list` | List semua mod di manifest |
| `dlavie-dlc delete <mod_id> <version>` | Hapus versi dari manifest |
| `dlavie-dlc new <ModName>` | Buat folder mod baru dari template |
| `dlavie-dlc help` | Tampilkan help |

## 🛡️ Keamanan

- ✅ Source code Launcher ada di repo **private** (`F16-Launcher`) — public tidak bisa lihat
- ✅ GitHub Token disimpan di `~/.bashrc` Termux (local di HP Anda)
- ✅ Repo `DLavie-Launcher-Data` (public) hanya berisi manifest + asset release
- ✅ Manifest tidak expose source code, hanya URL download + metadata
- ⚠️ **JANGAN share GitHub Token Anda ke siapapun**

## ❓ FAQ

**Q: Apakah butuh internet setiap kali upload?**
A: Ya, script perlu upload ZIP ke GitHub dan update manifest.

**Q: Berapa ukuran max DLC ZIP?**
A: 2GB per file (limit GitHub Release asset). DLC biasanya <1MB jadi aman.

**Q: Bagaimana kalau ingin rollback ke versi lama?**
A: Semua versi tersimpan di array `versions[]` di manifest. Edit manual manifest.json di repo, ubah `latest_version` ke versi lama.

**Q: Apakah user perlu install ulang Launcher untuk dapat update DLC?**
A: **TIDAK**. Launcher fetch manifest tiap 15 menit, jadi user tinggal buka app, tunggu refresh, lalu tap Update di DLC tab.

**Q: Bisakah upload DLC dari HP tanpa Termux?**
A: Bisa, tapi ribet — harus manual upload ZIP via browser ke GitHub release, lalu edit manifest.json via GitHub web UI. Termux jauh lebih cepat (1 command).

## 📞 Bantuan

Kalau ada error atau pertanyaan, screenshot errornya dan kirim ke chat. Saya akan bantu debug.
