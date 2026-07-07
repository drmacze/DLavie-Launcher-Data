#!/usr/bin/env python3
"""
DLavie Game Data Uploader — Upload data FIFA 16 baru ke release v26.

Usage:
  python upload_game_data.py <zip_file> [--sceneassets]
  python upload_game_data.py --list

Examples:
  # Upload dlavie26-data.zip baru (replace yang lama)
  python upload_game_data.py /sdcard/Download/dlavie26-data.zip

  # Upload sceneassets.zip (asset baru, optional)
  python upload_game_data.py /sdcard/Download/dlavie26-sceneassets.zip --sceneassets

  # Lihat status asset data di release v26
  python upload_game_data.py --list

Workflow:
  1. Hitung SHA-256 file zip baru
  2. Hapus asset lama dengan nama sama di release v26
  3. Upload file zip baru ke release v26
  4. Update manifest.json dengan size + SHA-256 baru
  5. Commit & push manifest
  6. Launcher user akan auto-detect versi baru (via manifest SHA berubah)
"""
import argparse
import base64
import hashlib
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# ─── Config ───────────────────────────────────────────────────────────────────
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN')
if not GITHUB_TOKEN:
    print('ERROR: GITHUB_TOKEN environment variable not set.')
    print('Setup: echo "export GITHUB_TOKEN=ghp_xxxxx" >> ~/.bashrc && source ~/.bashrc')
    sys.exit(1)

DATA_REPO = 'drmacze/DLavie-Launcher-Data'
RELEASE_TAG = 'v26'
BRANCH = 'main'

# Asset names di release v26
DATA_ZIP_NAME = 'dlavie26-data.zip'
SCENEASSETS_ZIP_NAME = 'dlavie26-sceneassets.zip'


def github_request(method, url, data=None, content_type='application/json'):
    """GitHub API request helper."""
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
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
        with urllib.request.urlopen(req, timeout=600) as resp:  # 10 min timeout untuk upload besar
            text = resp.read().decode('utf-8', errors='replace')
            return resp.status, json.loads(text) if text else {}
    except urllib.error.HTTPError as e:
        err = e.read().decode('utf-8', errors='replace')
        return e.code, {'error': err}


def sha256_file(path):
    """Hitung SHA-256 file dengan progress."""
    h = hashlib.sha256()
    size = Path(path).stat().st_size
    read = 0
    with open(path, 'rb') as f:
        while True:
            chunk = f.read(1024 * 1024)  # 1MB chunks
            if not chunk:
                break
            h.update(chunk)
            read += len(chunk)
            pct = (read / size) * 100 if size > 0 else 100
            print(f'\r  SHA-256: {pct:.1f}% ({read // 1024 // 1024} MB / {size // 1024 // 1024} MB)', end='', flush=True)
    print()
    return h.hexdigest()


def get_release_info():
    """Get release v26 info."""
    url = f'https://api.github.com/repos/{DATA_REPO}/releases/tags/{RELEASE_TAG}'
    status, body = github_request('GET', url)
    if status != 200:
        raise RuntimeError(f'Gagal fetch release {RELEASE_TAG}: {body}')
    return body


def delete_asset(asset_id, asset_name):
    """Delete asset dari release."""
    url = f'https://api.github.com/repos/{DATA_REPO}/releases/assets/{asset_id}'
    status, _ = github_request('DELETE', url)
    return status == 204


def upload_asset(upload_url, zip_path, asset_name):
    """Upload file zip ke release dengan progress."""
    url = f'{upload_url}?name={urllib.parse.quote(asset_name)}'
    file_size = Path(zip_path).stat().st_size
    print(f'  Upload {asset_name} ({file_size:,} bytes / {file_size / 1024 / 1024:.1f} MB)...')

    # Untuk file besar, kita tetap upload sekaligus (GitHub support sampai 2GB per asset)
    zip_bytes = Path(zip_path).read_bytes()
    status, body = github_request('POST', url, data=zip_bytes, content_type='application/zip')
    if status not in (200, 201):
        raise RuntimeError(f'Gagal upload: HTTP {status} — {body}')
    return body


def update_manifest_data_zip(size, sha256):
    """Update manifest.json: update dlavie26-data.zip entry."""
    # Fetch manifest
    url = f'https://api.github.com/repos/{DATA_REPO}/contents/manifest.json?ref={BRANCH}'
    status, body = github_request('GET', url)
    if status != 200:
        raise RuntimeError(f'Gagal fetch manifest: {body}')
    existing_sha = body['sha']
    manifest = json.loads(base64.b64decode(body['content']).decode('utf-8'))

    # Update core_files entry
    for f in manifest.get('game_data', {}).get('core_files', []):
        if f['name'] == DATA_ZIP_NAME:
            f['size'] = size
            f['sha256'] = sha256
            f['url'] = f'https://github.com/{DATA_REPO}/releases/download/{RELEASE_TAG}/{DATA_ZIP_NAME}'
            if 'note' not in f:
                f['note'] = 'Data inti FIFA 16. Berisi: cl.ini, ai.ini, data/flows, data/ux, data/db, audio, sceneassets, dll.'
            break

    # Update timestamp
    from datetime import datetime, timezone
    manifest['updated_at'] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    # Upload manifest
    content_b64 = base64.b64encode(json.dumps(manifest, indent=2).encode('utf-8')).decode('ascii')
    payload = {
        'message': f'chore(data): update {DATA_ZIP_NAME}\n\nSize: {size} bytes\nSHA-256: {sha256}',
        'content': content_b64,
        'branch': BRANCH,
        'sha': existing_sha,
    }
    url = f'https://api.github.com/repos/{DATA_REPO}/contents/manifest.json'
    status, body = github_request('PUT', url, data=payload)
    if status not in (200, 201):
        raise RuntimeError(f'Gagal update manifest: {body}')
    return body['commit']['sha']


def update_manifest_sceneassets(size, sha256):
    """Update manifest.json: update dlavie26-sceneassets.zip entry (optional_files)."""
    url = f'https://api.github.com/repos/{DATA_REPO}/contents/manifest.json?ref={BRANCH}'
    status, body = github_request('GET', url)
    if status != 200:
        raise RuntimeError(f'Gagal fetch manifest: {body}')
    existing_sha = body['sha']
    manifest = json.loads(base64.b64decode(body['content']).decode('utf-8'))

    # Update optional_files entry
    found = False
    for f in manifest.get('game_data', {}).get('optional_files', []):
        if f['name'] == SCENEASSETS_ZIP_NAME:
            f['size'] = size
            f['sha256'] = sha256
            f['url'] = f'https://github.com/{DATA_REPO}/releases/download/{RELEASE_TAG}/{SCENEASSETS_ZIP_NAME}'
            f['estimated_size_mb'] = size // 1024 // 1024
            found = True
            break

    if not found:
        # Tambah entry baru kalau belum ada
        if 'optional_files' not in manifest.get('game_data', {}):
            manifest['game_data']['optional_files'] = []
        manifest['game_data']['optional_files'].append({
            'type': 'data_zip',
            'name': SCENEASSETS_ZIP_NAME,
            'url': f'https://github.com/{DATA_REPO}/releases/download/{RELEASE_TAG}/{SCENEASSETS_ZIP_NAME}',
            'size': size,
            'sha256': sha256,
            'extract_to': 'Android/data/com.ea.gp.fifaworld/files/data/sceneassets/',
            'required': False,
            'optional': True,
            'description': 'HD Sceneassets (faces, kits, balls, stadiums, climate). Optional.',
            'estimated_size_mb': size // 1024 // 1024,
        })

    from datetime import datetime, timezone
    manifest['updated_at'] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    content_b64 = base64.b64encode(json.dumps(manifest, indent=2).encode('utf-8')).decode('ascii')
    payload = {
        'message': f'chore(data): update {SCENEASSETS_ZIP_NAME}\n\nSize: {size} bytes\nSHA-256: {sha256}',
        'content': content_b64,
        'branch': BRANCH,
        'sha': existing_sha,
    }
    url = f'https://api.github.com/repos/{DATA_REPO}/contents/manifest.json'
    status, body = github_request('PUT', url, data=payload)
    if status not in (200, 201):
        raise RuntimeError(f'Gagal update manifest: {body}')
    return body['commit']['sha']


def cmd_upload(zip_path, is_sceneassets=False):
    """Upload data zip ke release v26."""
    zip_path = Path(zip_path)
    if not zip_path.exists():
        print(f'ERROR: File tidak ditemukan: {zip_path}')
        sys.exit(1)

    asset_name = SCENEASSETS_ZIP_NAME if is_sceneassets else DATA_ZIP_NAME
    file_size = zip_path.stat().st_size

    print(f'=== Upload Game Data ===')
    print(f'  File: {zip_path}')
    print(f'  Asset name: {asset_name}')
    print(f'  Size: {file_size:,} bytes ({file_size / 1024 / 1024:.1f} MB)')
    print(f'  Type: {"Optional (sceneassets)" if is_sceneassets else "Required (core data)"}')
    print()

    # Step 1: Hitung SHA-256
    print('Step 1: Hitung SHA-256...')
    sha256 = sha256_file(zip_path)
    print(f'  SHA-256: {sha256}')
    print()

    # Step 2: Get release v26 info
    print('Step 2: Fetch release v26 info...')
    release = get_release_info()
    upload_url = release['upload_url'].split('{')[0]
    print(f'  Release ID: {release["id"]}')
    print()

    # Step 3: Hapus asset lama dengan nama sama
    print(f'Step 3: Cek & hapus asset lama ({asset_name})...')
    for asset in release.get('assets', []):
        if asset['name'] == asset_name:
            print(f'  Hapus: {asset["name"]} (id={asset["id"]}, {asset["size"]:,} bytes)')
            if delete_asset(asset['id'], asset['name']):
                print(f'  ✓ Dihapus')
            else:
                print(f'  ⚠ Gagal hapus, coba upload tetap lanjut')
    print()

    # Step 4: Upload file baru
    print(f'Step 4: Upload {asset_name}...')
    asset = upload_asset(upload_url, zip_path, asset_name)
    asset_url = asset['browser_download_url']
    print(f'  ✓ Uploaded!')
    print(f'    URL: {asset_url}')
    print(f'    Size: {asset["size"]:,} bytes')
    print()

    # Step 5: Update manifest
    print(f'Step 5: Update manifest.json...')
    if is_sceneassets:
        commit_sha = update_manifest_sceneassets(file_size, sha256)
    else:
        commit_sha = update_manifest_data_zip(file_size, sha256)
    print(f'  ✓ Manifest updated! Commit: {commit_sha[:8]}')
    print()

    # Summary
    print(f'=== SELESAI ===')
    print(f'  {asset_name} berhasil di-upload ke release {RELEASE_TAG}')
    print(f'  URL: {asset_url}')
    print(f'  SHA-256: {sha256}')
    print(f'  Size: {file_size:,} bytes ({file_size / 1024 / 1024:.1f} MB)')
    print()
    if is_sceneassets:
        print(f'  User Launcher v7.9.43+ akan dapat opsi "Download HD Sceneassets"')
        print(f'  User Launcher lama tetap bisa main tanpa sceneassets')
    else:
        print(f'  User Launcher akan auto-detect data baru via manifest')
        print(f'  Saat install fresh, akan download data zip yang baru')


def cmd_list():
    """List asset data di release v26."""
    print(f'=== Asset Data di Release {RELEASE_TAG} ===\n')
    release = get_release_info()
    print(f'Release: {release["name"]} (id={release["id"]})')
    print(f'URL: {release["html_url"]}')
    print()
    print(f'Assets ({len(release.get("assets", []))}):')
    for a in release.get('assets', []):
        size_mb = a['size'] / 1024 / 1024
        print(f'  - {a["name"]}')
        print(f'    Size: {a["size"]:,} bytes ({size_mb:.1f} MB)')
        print(f'    Downloads: {a["download_count"]}')
        print(f'    Updated: {a["created_at"]}')
        print(f'    URL: {a["browser_download_url"]}')
        print()


def main():
    parser = argparse.ArgumentParser(
        description='DLavie Game Data Uploader — Upload data FIFA 16 ke release v26',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Upload data inti baru (replace dlavie26-data.zip)
  python upload_game_data.py /sdcard/Download/dlavie26-data.zip

  # Upload sceneassets (asset baru, optional)
  python upload_game_data.py /sdcard/Download/dlavie26-sceneassets.zip --sceneassets

  # Lihat status asset data
  python upload_game_data.py --list
""",
    )
    parser.add_argument('zip_file', nargs='?', help='Path ke file zip yang akan di-upload')
    parser.add_argument('--sceneassets', action='store_true', help='Upload sebagai sceneassets (optional file)')
    parser.add_argument('--list', action='store_true', help='List asset data di release v26')

    args = parser.parse_args()

    if args.list:
        cmd_list()
        return

    if not args.zip_file:
        parser.print_help()
        sys.exit(1)

    cmd_upload(args.zip_file, args.sceneassets)


if __name__ == '__main__':
    main()
