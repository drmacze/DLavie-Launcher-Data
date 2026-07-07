#!/usr/bin/env python3
"""
DLavie DLC Updater — 1 command untuk upload DLC mod baru + auto-update manifest.

Usage:
  python update_dlc.py <mod_folder> <version> [--title "Title"] [--critical] [--note "Release note"]
  python update_dlc.py --list
  python update_dlc.py --delete <mod_id> <version>

Examples:
  # Upload versi baru DLC SaveMenuEnhancer
  python update_dlc.py DLC_SaveMenuEnhancer 1.0.1

  # Upload dengan release note custom
  python update_dlc.py DLC_SaveMenuEnhancer 1.0.2 --note "Fix Save dialog crash on Android 11"

  # List semua mod di manifest
  python update_dlc.py --list

  # Hapus versi tertentu
  python update_dlc.py --delete save-menu-enhancer 1.0.0

Workflow:
  1. Package folder mod jadi ZIP dengan nama {ModFolder}_v{Version}.zip
  2. Calculate SHA-256
  3. Upload ZIP ke release v26 di GitHub (replace jika sudah ada)
  4. Update manifest.json di repo DLavie-Launcher-Data main branch:
     - Tambah entry ke versions[] array
     - Update latest_version
  5. Commit & push manifest.json
  6. Launcher akan auto-fetch manifest di buka app berikutnya

Requirements:
  - Folder mod berisi file game (cl.ini, data/, dll)
  - GitHub PAT di env var GITHUB_TOKEN atau hardcode di bawah
"""
import argparse
import base64
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

# ─── Config ───────────────────────────────────────────────────────────────────
# GITHUB_TOKEN WAJIB di-set via env var. Jangan hardcode di sini!
# Setup di Termux: echo "export GITHUB_TOKEN=ghp_xxxxx" >> ~/.bashrc
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN')
if not GITHUB_TOKEN:
    print('ERROR: GITHUB_TOKEN environment variable not set.')
    print('Setup:')
    print('  1. Dapatkan token dari https://github.com/settings/tokens')
    print('  2. Jalankan: echo "export GITHUB_TOKEN=ghp_xxxxx" >> ~/.bashrc')
    print('  3. Reload: source ~/.bashrc')
    sys.exit(1)
DATA_REPO = 'drmacze/DLavie-Launcher-Data'  # repo public untuk manifest + release assets
RELEASE_TAG = 'v26'  # permanent release tag
BRANCH = 'main'
MANIFEST_LOCAL_PATH = Path(os.environ.get('MANIFEST_LOCAL_PATH', '/sdcard/dlavie-dlc/manifest.json'))
DOWNLOAD_DIR = Path(os.environ.get('DOWNLOAD_DIR', '/sdcard/dlavie-dlc/downloads'))

# ─── Helpers ──────────────────────────────────────────────────────────────────

def github_request(method, url, token=GITHUB_TOKEN, data=None, content_type='application/json'):
    """GitHub API request helper."""
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
    }
    if content_type:
        headers['Content-Type'] = content_type
    body = None
    if data is not None:
        body = data if isinstance(data, bytes) else json.dumps(data).encode('utf-8')
    req = urllib.request.Request(url, data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            text = resp.read().decode('utf-8', errors='replace')
            return resp.status, json.loads(text) if text else {}
    except urllib.error.HTTPError as e:
        err = e.read().decode('utf-8', errors='replace')
        return e.code, {'error': err}


def fetch_manifest():
    """Fetch manifest.json dari repo."""
    raw_url = f'https://raw.githubusercontent.com/{DATA_REPO}/{BRANCH}/manifest.json'
    req = urllib.request.Request(raw_url, method='GET')
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode('utf-8'))


def get_release_info():
    """Get release v26 info."""
    url = f'https://api.github.com/repos/{DATA_REPO}/releases/tags/{RELEASE_TAG}'
    status, body = github_request('GET', url)
    if status != 200:
        raise RuntimeError(f'Gagal fetch release {RELEASE_TAG}: {body}')
    return body


def delete_asset(asset_id):
    """Delete asset dari release."""
    url = f'https://api.github.com/repos/{DATA_REPO}/releases/assets/{asset_id}'
    status, body = github_request('DELETE', url)
    return status == 204


def upload_asset(upload_url, zip_path, asset_name):
    """Upload ZIP sebagai release asset."""
    url = f'{upload_url}?name={urllib.parse.quote(asset_name)}'
    zip_bytes = Path(zip_path).read_bytes()
    status, body = github_request('POST', url, data=zip_bytes, content_type='application/zip')
    if status not in (200, 201):
        raise RuntimeError(f'Gagal upload asset: HTTP {status} — {body}')
    return body


def package_zip(mod_folder, version):
    """Package folder mod jadi ZIP."""
    mod_folder = Path(mod_folder)
    if not mod_folder.exists() or not mod_folder.is_dir():
        raise RuntimeError(f'Folder mod tidak ditemukan: {mod_folder}')

    # Nama mod dari folder name (contoh: DLC_SaveMenuEnhancer → save-menu-enhancer)
    folder_name = mod_folder.name
    mod_id = re.sub(r'^DLC_', '', folder_name).replace('_', '-').lower()
    asset_name = f'{folder_name}_v{version}.zip'
    zip_path = DOWNLOAD_DIR / asset_name

    # Kumpulkan file yang akan di-zip (semua file di folder, skip manifest.json/README.md)
    skip_files = {'manifest.json', 'README.md', '.gitignore', '.git', 'reference'}
    files_to_zip = []
    for root, dirs, files in os.walk(mod_folder):
        # Skip .git and reference folders
        dirs[:] = [d for d in dirs if d not in skip_files]
        for f in files:
            if f in skip_files:
                continue
            full_path = Path(root) / f
            rel_path = full_path.relative_to(mod_folder)
            files_to_zip.append((full_path, rel_path))

    if not files_to_zip:
        raise RuntimeError(f'Folder mod kosong: {mod_folder}')

    # Buat ZIP
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for full_path, rel_path in files_to_zip:
            arcname = str(rel_path).replace('\\', '/')
            zf.write(full_path, arcname)
            print(f'  + {arcname}')

    # Calculate SHA-256
    sha256 = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    size = zip_path.stat().st_size

    return {
        'zip_path': zip_path,
        'asset_name': asset_name,
        'sha256': sha256,
        'size': size,
        'mod_id': mod_id,
    }


def update_manifest_in_repo(mod_id, version, asset_url, sha256, size, title=None, note=None, critical=False):
    """Update manifest.json di repo: tambah version baru + update latest_version."""
    # Fetch manifest dari repo (selalu fresh)
    manifest = fetch_manifest()
    manifest_local = MANIFEST_LOCAL_PATH
    manifest_local.write_text(json.dumps(manifest, indent=2))

    # Cari mod by id
    mod = None
    for m in manifest.get('mods', []):
        if m['id'] == mod_id:
            mod = m
            break

    now_iso = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    if mod is None:
        # Mod baru — buat entry
        print(f'\n  Mod baru terdeteksi: {mod_id}')
        mod_name = title or f'DLC: {mod_id.replace("-", " ").title()}'
        mod = {
            'id': mod_id,
            'slug': mod_id,
            'name': mod_name,
            'title': f'{mod_name} v{version}',
            'description': 'Auto-generated by update_dlc.py. Edit manifest.json manual untuk deskripsi lengkap.',
            'category': 'gameplay_enhancement',
            'author': 'DLavie Team',
            'icon': 'extension',
            'latest_version': version,
            'version_code': int(time.time()),
            'channel': 'stable',
            'published': True,
            'critical': critical,
            'restart_game_required': False,
            'risk_level': 'low',
            'min_launcher_version_code': 206,
            'target_game_package': 'com.ea.gp.fifaworld',
            'released_at': now_iso,
            'body': f'## {mod_name} v{version}\n\nAuto-uploaded by update_dlc.py.',
            'release_notes': [note] if note else [f'Initial release v{version}'],
            'known_issues': [],
            'files_modified': [],
            'files_added': [],
            'versions': []
        }
        manifest['mods'].append(mod)
    else:
        # Mod existing — update title kalau perlu
        if title:
            mod['title'] = f'{title} v{version}'
            mod['name'] = title

    # Cek apakah versi sudah ada
    existing_version = None
    for v in mod.get('versions', []):
        if v['version'] == version:
            existing_version = v
            break

    version_entry = {
        'version': version,
        'version_code': mod.get('version_code', int(time.time())),
        'released_at': now_iso,
        'url': asset_url,
        'sha256': sha256,
        'size': size,
        'channel': 'stable',
        'critical': critical,
    }

    if existing_version:
        # Replace existing version
        print(f'\n  Versi {version} sudah ada, replace...')
        mod['versions'] = [version_entry if v['version'] == version else v for v in mod['versions']]
    else:
        # Tambah version baru di awal array (paling baru di depan)
        mod['versions'].insert(0, version_entry)

    # Update latest_version
    mod['latest_version'] = version
    mod['critical'] = critical
    if note:
        mod['release_notes'].insert(0, note)
        # Keep max 10 release notes
        mod['release_notes'] = mod['release_notes'][:10]

    # Update manifest timestamp
    manifest['updated_at'] = now_iso

    # Save locally
    manifest_local.write_text(json.dumps(manifest, indent=2))
    print(f'\n  Manifest lokal diupdate: {manifest_local}')

    # Upload ke repo via Contents API (perlu sha jika file sudah ada)
    check_url = f'https://api.github.com/repos/{DATA_REPO}/contents/manifest.json?ref={BRANCH}'
    status, body = github_request('GET', check_url)
    existing_sha = body.get('sha') if status == 200 else None

    content_b64 = base64.b64encode(manifest_local.read_bytes()).decode('ascii')
    payload = {
        'message': f'chore(mods): {mod_id} v{version}\n\n- Update latest_version to {version}\n- SHA-256: {sha256[:16]}...\n- Size: {size} bytes',
        'content': content_b64,
        'branch': BRANCH,
    }
    if existing_sha:
        payload['sha'] = existing_sha

    upload_url = f'https://api.github.com/repos/{DATA_REPO}/contents/manifest.json'
    status, body = github_request('PUT', upload_url, data=payload)
    if status not in (200, 201):
        raise RuntimeError(f'Gagal update manifest.json: HTTP {status} — {body}')

    print(f'  ✓ Manifest diupload ke repo: commit {body["commit"]["sha"][:8]}')
    return manifest


def cmd_upload(mod_folder, version, title=None, note=None, critical=False):
    """Upload DLC baru."""
    print(f'=== Upload DLC ===')
    print(f'  Folder: {mod_folder}')
    print(f'  Version: {version}')
    if title:
        print(f'  Title: {title}')
    if note:
        print(f'  Note: {note}')
    print()

    # Step 1: Package ZIP
    print('Step 1: Package ZIP...')
    info = package_zip(mod_folder, version)
    print(f'  ✓ ZIP: {info["asset_name"]}')
    print(f'    Size: {info["size"]} bytes')
    print(f'    SHA-256: {info["sha256"]}')
    print(f'    Mod ID: {info["mod_id"]}')

    # Step 2: Get release v26 info
    print('\nStep 2: Get release v26 info...')
    release = get_release_info()
    upload_url = release['upload_url'].split('{')[0]
    print(f'  Release ID: {release["id"]}')

    # Step 3: Hapus asset lama dengan nama sama (jika ada)
    print('\nStep 3: Cek & hapus asset lama...')
    for asset in release.get('assets', []):
        if asset['name'] == info['asset_name']:
            print(f'  Hapus asset lama: {asset["name"]} (id={asset["id"]})')
            delete_asset(asset['id'])

    # Step 4: Upload ZIP ke release v26
    print('\nStep 4: Upload ZIP ke release v26...')
    asset = upload_asset(upload_url, info['zip_path'], info['asset_name'])
    asset_url = asset['browser_download_url']
    print(f'  ✓ Asset uploaded!')
    print(f'    URL: {asset_url}')

    # Step 5: Update manifest.json di repo
    print('\nStep 5: Update manifest.json...')
    update_manifest_in_repo(
        mod_id=info['mod_id'],
        version=version,
        asset_url=asset_url,
        sha256=info['sha256'],
        size=info['size'],
        title=title,
        note=note,
        critical=critical,
    )

    # Step 6: Summary
    print('\n=== SELESAI ===')
    print(f'  DLC: {info["mod_id"]} v{version}')
    print(f'  Download URL: {asset_url}')
    print(f'  SHA-256: {info["sha256"]}')
    print(f'  Size: {info["size"]} bytes')
    print(f'  Manifest: https://raw.githubusercontent.com/{DATA_REPO}/{BRANCH}/manifest.json')
    print()
    print('Launcher akan auto-fetch manifest dalam 5 menit (cached) atau saat user buka app berikutnya.')


def cmd_list():
    """List semua mod di manifest."""
    print('=== Mod List ===\n')
    manifest = fetch_manifest()
    print(f'Manifest updated: {manifest.get("updated_at")}')
    print(f'Total mods: {len(manifest.get("mods", []))}')
    print()
    for mod in manifest.get('mods', []):
        print(f'  [{mod["id"]}]')
        print(f'    Name: {mod["name"]}')
        print(f'    Latest: v{mod["latest_version"]}')
        print(f'    Published: {mod["published"]}')
        print(f'    Critical: {mod["critical"]}')
        print(f'    Versions: {len(mod.get("versions", []))}')
        for v in mod.get('versions', []):
            print(f'      - v{v["version"]} ({v["size"]} bytes, {v["released_at"][:10]})')
        print()


def cmd_delete(mod_id, version):
    """Hapus versi tertentu dari manifest."""
    print(f'=== Delete {mod_id} v{version} ===\n')

    # Fetch manifest
    manifest = fetch_manifest()
    MANIFEST_LOCAL_PATH.write_text(json.dumps(manifest, indent=2))

    # Cari mod
    mod = None
    for m in manifest.get('mods', []):
        if m['id'] == mod_id:
            mod = m
            break

    if mod is None:
        print(f'  ✗ Mod {mod_id} tidak ditemukan')
        return

    # Hapus versi
    original_count = len(mod.get('versions', []))
    mod['versions'] = [v for v in mod.get('versions', []) if v['version'] != version]

    if len(mod['versions']) == original_count:
        print(f'  ✗ Versi {version} tidak ditemukan di mod {mod_id}')
        return

    # Update latest_version kalau yang dihapus adalah latest
    if mod['latest_version'] == version:
        if mod['versions']:
            mod['latest_version'] = mod['versions'][0]['version']
        else:
            mod['latest_version'] = ''
            mod['published'] = False

    # Update timestamp
    manifest['updated_at'] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    # Save & upload
    MANIFEST_LOCAL_PATH.write_text(json.dumps(manifest, indent=2))

    check_url = f'https://api.github.com/repos/{DATA_REPO}/contents/manifest.json?ref={BRANCH}'
    status, body = github_request('GET', check_url)
    existing_sha = body.get('sha') if status == 200 else None

    content_b64 = base64.b64encode(MANIFEST_LOCAL_PATH.read_bytes()).decode('ascii')
    payload = {
        'message': f'chore(mods): delete {mod_id} v{version}',
        'content': content_b64,
        'branch': BRANCH,
    }
    if existing_sha:
        payload['sha'] = existing_sha

    upload_url = f'https://api.github.com/repos/{DATA_REPO}/contents/manifest.json'
    status, body = github_request('PUT', upload_url, data=payload)
    if status not in (200, 201):
        raise RuntimeError(f'Gagal update manifest: HTTP {status} — {body}')

    print(f'  ✓ Versi {version} dihapus dari manifest')
    print(f'  Commit: {body["commit"]["sha"][:8]}')


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='DLavie DLC Updater — Upload DLC mod baru + auto-update manifest',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Upload versi baru
  python update_dlc.py DLC_SaveMenuEnhancer 1.0.1

  # Upload dengan note
  python update_dlc.py DLC_SaveMenuEnhancer 1.0.2 --note "Fix crash on Android 11"

  # List semua mod
  python update_dlc.py --list

  # Hapus versi
  python update_dlc.py --delete save-menu-enhancer 1.0.0
""",
    )
    parser.add_argument('mod_folder', nargs='?', help='Path ke folder mod (berisi cl.ini, data/, dll)')
    parser.add_argument('version', nargs='?', help='Version baru (contoh: 1.0.1)')
    parser.add_argument('--title', help='Title custom untuk mod')
    parser.add_argument('--note', help='Release note singkat untuk versi ini')
    parser.add_argument('--critical', action='store_true', help='Tandai sebagai critical update')
    parser.add_argument('--list', action='store_true', help='List semua mod di manifest')
    parser.add_argument('--delete', nargs=2, metavar=('MOD_ID', 'VERSION'), help='Hapus versi tertentu dari manifest')

    args = parser.parse_args()

    if args.list:
        cmd_list()
        return

    if args.delete:
        cmd_delete(args.delete[0], args.delete[1])
        return

    if not args.mod_folder or not args.version:
        parser.print_help()
        sys.exit(1)

    cmd_upload(args.mod_folder, args.version, args.title, args.note, args.critical)


if __name__ == '__main__':
    main()
