#!/data/data/com.termux/files/usr/bin/bash
# ============================================================
# DLavie DLC Manager — Termux Setup Script
# ============================================================
# Jalankan SEKALI saja setelah install Termux:
#   pkg install git -y && curl -sL https://raw.githubusercontent.com/drmacze/DLavie-Launcher-Data/main/termux-dlavie-dlc/setup/install.sh | bash
#
# Setelah setup selesai, Anda bisa upload DLC dengan 1 command:
#   dlavie-dlc upload MyMod 1.0.0 --note "Fitur baru"
#   dlavie-dlc list
#   dlavie-dlc delete my-mod 1.0.0
# ============================================================

set -e

echo "============================================================"
echo "  DLavie DLC Manager — Termux Setup"
echo "============================================================"
echo ""

# Step 1: Install dependencies
echo "[1/6] Install dependencies (python, git, curl)..."
pkg update -y >/dev/null 2>&1
pkg install -y python git curl openssh >/dev/null 2>&1
echo "  ✓ Dependencies installed"
echo ""

# Step 2: Setup working directory di /sdcard/dlavie-dlc
WORK_DIR="/sdcard/dlavie-dlc"
echo "[2/6] Setup working directory: $WORK_DIR"
mkdir -p "$WORK_DIR/bin"
mkdir -p "$WORK_DIR/mods"
mkdir -p "$WORK_DIR/template"
echo "  ✓ Folder created: $WORK_DIR"
echo "    - bin/    → script update_dlc.py"
echo "    - mods/   → folder kerja Anda untuk bikin DLC baru"
echo "    - template/ → contoh struktur mod"
echo ""

# Step 3: Download update_dlc.py + upload_game_data.py
echo "[3/6] Download scripts..."
curl -sL "https://raw.githubusercontent.com/drmacze/DLavie-Launcher-Data/main/termux-dlavie-dlc/bin/update_dlc.py" \
  -o "$WORK_DIR/bin/update_dlc.py"
curl -sL "https://raw.githubusercontent.com/drmacze/DLavie-Launcher-Data/main/termux-dlavie-dlc/bin/upload_game_data.py" \
  -o "$WORK_DIR/bin/upload_game_data.py"
chmod +x "$WORK_DIR/bin/update_dlc.py" "$WORK_DIR/bin/upload_game_data.py"
echo "  ✓ update_dlc.py downloaded"
echo "  ✓ upload_game_data.py downloaded"
echo ""

# Step 4: Download template mod contoh
echo "[4/6] Download template mod..."
curl -sL "https://raw.githubusercontent.com/drmacze/DLavie-Launcher-Data/main/termux-dlavie-dlc/template/example_mod/cl.ini" \
  -o "$WORK_DIR/template/cl.ini" 2>/dev/null || true
echo "  ✓ Template downloaded"
echo ""

# Step 5: Setup GitHub token (akan minta input user)
echo "[5/6] Setup GitHub Token..."
echo ""
echo "Untuk upload DLC, Anda butuh GitHub Personal Access Token (PAT)."
echo "Cara dapat:"
echo "  1. Buka https://github.com/settings/tokens di browser HP"
echo "  2. Login akun GitHub Anda (drmacze)"
echo "  3. Klik 'Generate new token (classic)'"
echo "  4. Beri nama: dlavie-dlc-termux"
echo "  5. Centang scope: repo (full control)"
echo "  6. Klik 'Generate token'"
echo "  7. Copy token (format: ghp_xxxxxxxxxxxx)"
echo ""
read -p "Paste GitHub token di sini: " GH_TOKEN
echo ""

if [ -z "$GH_TOKEN" ]; then
  echo "  ⚠ Token kosong, skip. Anda bisa set manual nanti:"
  echo "    echo 'export GITHUB_TOKEN=ghp_xxxx' >> ~/.bashrc"
else
  # Save token ke .bashrc
  if grep -q "GITHUB_TOKEN" ~/.bashrc 2>/dev/null; then
    sed -i '/GITHUB_TOKEN/d' ~/.bashrc
  fi
  echo "export GITHUB_TOKEN=$GH_TOKEN" >> ~/.bashrc
  export GITHUB_TOKEN=$GH_TOKEN
  echo "  ✓ Token saved to ~/.bashrc"
fi
echo ""

# Step 6: Buat wrapper command 'dlavie-dlc'
echo "[6/6] Buat wrapper command 'dlavie-dlc'..."
cat > "$PREFIX/bin/dlavie-dlc" << 'WRAPPER_EOF'
#!/data/data/com.termux/files/usr/bin/bash
# Wrapper untuk update_dlc.py + upload_game_data.py
# Usage:
#   dlavie-dlc upload <mod_folder> <version> [--note "..."]   Upload DLC mod baru
#   dlavie-dlc list                                            List mod di manifest
#   dlavie-dlc delete <mod_id> <version>                       Hapus versi mod
#   dlavie-dlc new <ModName>                                   Buat folder mod baru
#   dlavie-dlc upload-data <zip_file>                          Upload data inti FIFA 16
#   dlavie-dlc upload-data <zip_file> --sceneassets            Upload sceneassets (optional)
#   dlavie-dlc list-data                                       List asset data di release v26
#   dlavie-dlc help                                            Tampilkan help

WORK_DIR="/sdcard/dlavie-dlc"
PYTHON=python

case "$1" in
  upload)
    shift
    cd "$WORK_DIR"
    $PYTHON "$WORK_DIR/bin/update_dlc.py" "$@"
    ;;
  list)
    $PYTHON "$WORK_DIR/bin/update_dlc.py" --list
    ;;
  delete)
    shift
    $PYTHON "$WORK_DIR/bin/update_dlc.py" --delete "$@"
    ;;
  new)
    # Buat folder mod baru dari template
    if [ -z "$2" ]; then
      echo "Usage: dlavie-dlc new <ModName>"
      echo "Contoh: dlavie-dlc new DLC_MyNewFeature"
      exit 1
    fi
    MOD_NAME="$2"
    MOD_DIR="$WORK_DIR/mods/$MOD_NAME"
    if [ -d "$MOD_DIR" ]; then
      echo "✗ Folder sudah ada: $MOD_DIR"
      exit 1
    fi
    mkdir -p "$MOD_DIR/data"
    # Copy template cl.ini jika ada
    if [ -f "$WORK_DIR/template/cl.ini" ]; then
      cp "$WORK_DIR/template/cl.ini" "$MOD_DIR/cl.ini"
    fi
    cat > "$MOD_DIR/README.md" << EOF
# $MOD_NAME

## Versi: 0.0.1

## Deskripsi
TODO: Deskripsi mod ini

## File yang Dimodifikasi
- cl.ini
EOF
    echo "✓ Folder mod baru dibuat: $MOD_DIR"
    echo ""
    echo "Edit file di folder itu (pakai file manager atau text editor):"
    echo "  $MOD_DIR"
    echo ""
    echo "Setelah selesai edit, upload dengan:"
    echo "  dlavie-dlc upload $MOD_NAME 0.0.1 --note 'Initial release'"
    ;;
  upload-data)
    # Upload data FIFA 16 (data inti atau sceneassets)
    shift
    $PYTHON "$WORK_DIR/bin/upload_game_data.py" "$@"
    ;;
  list-data)
    # List asset data di release v26
    $PYTHON "$WORK_DIR/bin/upload_game_data.py" --list
    ;;
  help|--help|-h)
    echo "DLavie DLC Manager — Termux"
    echo ""
    echo "Commands:"
    echo "  dlavie-dlc upload <mod_folder> <version> [--note '...']   Upload DLC mod baru"
    echo "  dlavie-dlc list                                            List mod di manifest"
    echo "  dlavie-dlc delete <mod_id> <version>                       Hapus versi mod"
    echo "  dlavie-dlc new <ModName>                                   Buat folder mod baru"
    echo "  dlavie-dlc upload-data <zip_file>                          Upload data inti FIFA 16 (replace lama)"
    echo "  dlavie-dlc upload-data <zip_file> --sceneassets            Upload sceneassets (asset optional)"
    echo "  dlavie-dlc list-data                                       List asset data di release v26"
    echo "  dlavie-dlc help                                            Tampilkan help ini"
    echo ""
    echo "Contoh workflow DLC mod:"
    echo "  dlavie-dlc new DLC_MyFeature"
    echo "  # edit file di /sdcard/dlavie-dlc/mods/DLC_MyFeature/"
    echo "  dlavie-dlc upload DLC_MyFeature 1.0.0 --note 'Initial release'"
    echo "  dlavie-dlc list"
    echo ""
    echo "Contoh workflow upload data FIFA 16 baru:"
    echo "  # Upload data inti (replace dlavie26-data.zip lama)"
    echo "  dlavie-dlc upload-data /sdcard/Download/dlavie26-data.zip"
    echo ""
    echo "  # Upload sceneassets (asset baru, optional)"
    echo "  dlavie-dlc upload-data /sdcard/Download/dlavie26-sceneassets.zip --sceneassets"
    echo ""
    echo "  # Cek status asset data"
    echo "  dlavie-dlc list-data"
    echo ""
    echo "Working directory: /sdcard/dlavie-dlc"
    ;;
  *)
    echo "Unknown command: $1"
    echo "Run 'dlavie-dlc help' for usage."
    exit 1
    ;;
esac
WRAPPER_EOF
chmod +x "$PREFIX/bin/dlavie-dlc"
echo "  ✓ Command 'dlavie-dlc' siap dipakai"
echo ""

# Selesai
echo "============================================================"
echo "  ✅ Setup Selesai!"
echo "============================================================"
echo ""
echo "Sekarang Anda bisa kelola DLC langsung dari HP. Coba:"
echo ""
echo "  dlavie-dlc help          # lihat semua command"
echo "  dlavie-dlc list          # lihat mod yang sudah ada"
echo "  dlavie-dlc new DLC_Test  # buat folder mod baru"
echo ""
echo "Untuk upload DLC baru:"
echo "  1. Edit file mod di /sdcard/dlavie-dlc/mods/DLC_NamaMod/"
echo "  2. dlavie-dlc upload DLC_NamaMod 1.0.0 --note 'Initial release'"
echo ""
echo "Folder kerja: /sdcard/dlavie-dlc/"
echo "Buka dengan file manager Android untuk edit file mod."
echo ""
echo "Reopen Termux untuk load GITHUB_TOKEN, atau jalankan:"
echo "  source ~/.bashrc"
