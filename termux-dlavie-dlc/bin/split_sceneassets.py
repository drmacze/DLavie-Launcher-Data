#!/usr/bin/env python3
"""
DLavie Data Splitter — Pisahkan sceneassets dari dlavie26-data.zip

Gunakan script ini kalau Anda sudah punya dlavie26-data.zip dan ingin
memisahkan sceneassets jadi file terpisah (dlavie26-sceneassets.zip).

Cara pakai:
  python split_sceneassets.py <input_zip> [--output-dir /sdcard/dlavie-dlc/splits]

Output:
  - dlavie26-data-core.zip  (data inti tanpa sceneassets)
  - dlavie26-sceneassets.zip (sceneassets only)

Kalau Anda punya data FIFA 16 baru (bukan dari zip existing), jalankan:
  python split_sceneassets.py --from-folder /path/to/data/folder
"""
import argparse
import hashlib
import os
import sys
import zipfile
from pathlib import Path


def split_zip(input_zip, output_dir):
    """Pisahkan sceneassets dari zip existing."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    core_zip = output_dir / 'dlavie26-data-core.zip'
    sceneassets_zip = output_dir / 'dlavie26-sceneassets.zip'

    print(f'=== Split {input_zip} ===')
    print(f'  Output dir: {output_dir}')
    print()

    core_count = 0
    sceneassets_count = 0
    core_size = 0
    sceneassets_size = 0

    with zipfile.ZipFile(input_zip, 'r') as zin:
        with zipfile.ZipFile(core_zip, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zcore, \
             zipfile.ZipFile(sceneassets_zip, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zscene:

            for entry in zin.infolist():
                if entry.is_dir():
                    continue

                name = entry.filename
                # Deteksi sceneassets path (bisa berbagai format)
                is_sceneassets = (
                    '/sceneassets/' in name or
                    name.startswith('sceneassets/') or
                    name.startswith('data/sceneassets/') or
                    name.startswith('files/data/sceneassets/') or
                    name.startswith('Android/data/com.ea.gp.fifaworld/files/data/sceneassets/')
                )

                # Strip prefix supaya path relatif bersih
                clean_name = name
                for prefix in [
                    'Android/data/com.ea.gp.fifaworld/files/',
                    'Android/data/com.ea.gp.fifaworld/',
                    'files/',
                    './'
                ]:
                    if clean_name.startswith(prefix):
                        clean_name = clean_name[len(prefix):]
                        break

                data = zin.read(entry)

                if is_sceneassets:
                    # Tulis ke sceneassets zip dengan path relatif dari sceneassets/
                    scene_name = clean_name
                    if scene_name.startswith('data/sceneassets/'):
                        scene_name = scene_name[len('data/sceneassets/'):]
                    elif scene_name.startswith('sceneassets/'):
                        scene_name = scene_name[len('sceneassets/'):]

                    zscene.writestr(scene_name, data)
                    sceneassets_count += 1
                    sceneassets_size += len(data)
                    if sceneassets_count % 100 == 0:
                        print(f'  [sceneassets] {sceneassets_count} files... ({sceneassets_size // 1024 // 1024} MB)')
                else:
                    # Tulis ke core zip
                    zcore.writestr(clean_name, data)
                    core_count += 1
                    core_size += len(data)
                    if core_count % 1000 == 0:
                        print(f'  [core] {core_count} files... ({core_size // 1024 // 1024} MB)')

    print()
    print(f'=== Hasil Split ===')
    print(f'  Core: {core_zip.name}')
    print(f'    Files: {core_count}')
    print(f'    Size: {core_size:,} bytes ({core_size / 1024 / 1024:.1f} MB)')
    print(f'    SHA-256: {sha256_file(core_zip)}')
    print()
    print(f'  Sceneassets: {sceneassets_zip.name}')
    print(f'    Files: {sceneassets_count}')
    print(f'    Size: {sceneassets_size:,} bytes ({sceneassets_size / 1024 / 1024:.1f} MB)')
    print(f'    SHA-256: {sha256_file(sceneassets_zip)}')
    print()
    print(f'=== Langkah Selanjutnya ===')
    print(f'1. Upload kedua file ke release v26 di DLavie-Launcher-Data:')
    print(f'   - dlavie26-data-core.zip (replace dlavie26-data.zip yang lama)')
    print(f'   - dlavie26-sceneassets.zip (asset baru)')
    print(f'2. Update manifest.json dengan ukuran + SHA-256 baru')
    print(f'3. Launcher akan auto-detect dan tampilkan tombol "Download Sceneassets (Optional)"')


def split_folder(input_folder, output_dir):
    """Buat 2 zip dari folder data FIFA 16."""
    input_folder = Path(input_folder)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    core_zip = output_dir / 'dlavie26-data-core.zip'
    sceneassets_zip = output_dir / 'dlavie26-sceneassets.zip'

    print(f'=== Zip dari folder: {input_folder} ===')
    print(f'  Output: {output_dir}')
    print()

    # Kumpulkan file
    core_files = []
    sceneassets_files = []

    for root, dirs, files in os.walk(input_folder):
        # Skip .git, __pycache__, etc
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', '.cache']]
        for f in files:
            full = Path(root) / f
            rel = full.relative_to(input_folder)
            rel_str = str(rel).replace('\\', '/')

            # Cek apakah file sceneassets
            is_sceneassets = (
                'sceneassets/' in rel_str and
                not rel_str.startswith('data/ux/') and  # ux bukan sceneassets
                not rel_str.startswith('data/flows/')   # flows bukan sceneassets
            )

            if is_sceneassets:
                sceneassets_files.append((full, rel))
            else:
                core_files.append((full, rel))

    print(f'  Core files: {len(core_files)}')
    print(f'  Sceneassets files: {len(sceneassets_files)}')
    print()

    # Zip core
    print('Zipping core...')
    core_size = 0
    with zipfile.ZipFile(core_zip, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for i, (full, rel) in enumerate(core_files, 1):
            arcname = str(rel).replace('\\', '/')
            zf.write(full, arcname)
            core_size += full.stat().st_size
            if i % 500 == 0:
                print(f'  [{i}/{len(core_files)}] {arcname}')

    print(f'  Core size: {core_size:,} bytes ({core_size / 1024 / 1024:.1f} MB)')
    print(f'  Core SHA-256: {sha256_file(core_zip)}')
    print()

    # Zip sceneassets
    print('Zipping sceneassets...')
    scene_size = 0
    with zipfile.ZipFile(sceneassets_zip, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for i, (full, rel) in enumerate(sceneassets_files, 1):
            # Strip sceneassets/ prefix supaya path relatif di dalam zip
            arcname = str(rel).replace('\\', '/')
            if arcname.startswith('data/sceneassets/'):
                arcname = arcname[len('data/sceneassets/'):]
            elif arcname.startswith('sceneassets/'):
                arcname = arcname[len('sceneassets/'):]

            zf.write(full, arcname)
            scene_size += full.stat().st_size
            if i % 100 == 0:
                print(f'  [{i}/{len(sceneassets_files)}] {arcname}')

    print(f'  Sceneassets size: {scene_size:,} bytes ({scene_size / 1024 / 1024:.1f} MB)')
    print(f'  Sceneassets SHA-256: {sha256_file(sceneassets_zip)}')
    print()

    print(f'=== Hasil ===')
    print(f'  {core_zip.name}: {core_zip.stat().st_size / 1024 / 1024:.1f} MB')
    print(f'  {sceneassets_zip.name}: {sceneassets_zip.stat().st_size / 1024 / 1024:.1f} MB')


def sha256_file(path):
    """Hitung SHA-256 file."""
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(
        description='DLavie Data Splitter — Pisahkan sceneassets dari data FIFA 16',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Split dari zip existing
  python split_sceneassets.py dlavie26-data.zip

  # Split dari folder data
  python split_sceneassets.py --from-folder /path/to/data --output-dir /sdcard/dlavie-dlc/splits

  # Custom output dir
  python split_sceneassets.py dlavie26-data.zip --output-dir /tmp/splits
""",
    )
    parser.add_argument('input_zip', nargs='?', help='Path ke dlavie26-data.zip yang akan di-split')
    parser.add_argument('--from-folder', help='Buat zip dari folder data FIFA 16 (bukan dari zip existing)')
    parser.add_argument('--output-dir', default='/sdcard/dlavie-dlc/splits', help='Output directory (default: /sdcard/dlavie-dlc/splits)')

    args = parser.parse_args()

    if args.from_folder:
        split_folder(args.from_folder, args.output_dir)
    elif args.input_zip:
        if not Path(args.input_zip).exists():
            print(f'ERROR: File tidak ditemukan: {args.input_zip}')
            sys.exit(1)
        split_zip(args.input_zip, args.output_dir)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
