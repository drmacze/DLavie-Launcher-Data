#!/usr/bin/env python3
"""
DLavie Sceneassets Splitter — Pisahkan sceneassets 6GB jadi beberapa zip per kategori.

Solusi untuk GitHub Release limit 2GB per file. Sceneassets 6GB di-split jadi:
- sceneassets-faces.zip      (biasanya 2-3GB)
- sceneassets-kit.zip        (1-2GB)
- sceneassets-stadium.zip    (500MB-1GB)
- sceneassets-hair.zip       (200-500MB)
- sceneassets-ball.zip       (50-100MB)
- sceneassets-shoe.zip       (50-100MB)
- sceneassets-climate.zip    (22MB)
- sceneassets-body.zip       (5MB)
- sceneassets-misc.zip       (sisanya)

Cara pakai:
  python split_sceneassets_by_category.py <sceneassets_folder> [--output-dir /sdcard/dlavie-dlc/splits]

Contoh:
  python split_sceneassets_by_category.py /sdcard/FIFA16/data/sceneassets
  python split_sceneassets_by_category.py /sdcard/FIFA16/data/sceneassets --output-dir /tmp/splits
"""
import argparse
import hashlib
import os
import sys
import zipfile
from pathlib import Path

# ─── Config ───────────────────────────────────────────────────────────────────

# Kategori sceneassets yang akan di-split jadi file terpisah
# Setiap kategori jadi 1 zip file
# Kategori "misc" menampung semua yang tidak masuk kategori utama
CATEGORIES = {
    'faces': ['faces'],
    'kit': ['kit'],
    'stadium': ['stadium'],
    'hair': ['hair', 'hairlod'],
    'ball': ['ball'],
    'shoe': ['shoe'],
    'body': ['body', 'charactercmn', 'heads'],
    'climate': ['climate', 'sky'],
    'pitch': ['pitch'],
    'crowd': ['crowdplacement'],
    'accessory': ['accessory', 'gkglove', 'adboard'],
    'presentation': ['presentation', 'wipe3d', 'fe'],
}

# Kategori yang "kecil" digabung jadi 1 zip "misc" supaya tidak terlalu banyak file
# Threshold: kalau total size kategori < 50MB, gabung ke misc
MISC_THRESHOLD = 50 * 1024 * 1024  # 50MB


def sha256_file(path):
    """Hitung SHA-256 file."""
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def format_size(bytes):
    """Format bytes ke human readable."""
    if bytes >= 1024 * 1024 * 1024:
        return f'{bytes / 1024 / 1024 / 1024:.2f} GB'
    elif bytes >= 1024 * 1024:
        return f'{bytes / 1024 / 1024:.1f} MB'
    elif bytes >= 1024:
        return f'{bytes / 1024:.1f} KB'
    return f'{bytes} B'


def split_sceneassets(input_folder, output_dir):
    """Split sceneassets folder jadi beberapa zip per kategori."""
    input_folder = Path(input_folder)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_folder.exists() or not input_folder.is_dir():
        print(f'ERROR: Folder tidak ditemukan: {input_folder}')
        sys.exit(1)

    print(f'=== Split Sceneassets ===')
    print(f'  Input: {input_folder}')
    print(f'  Output: {output_dir}')
    print()

    # Kumpulkan file per kategori
    # category_files = {category_name: [(file_path, arcname), ...]}
    category_files = {}
    misc_files = []
    uncategorized_files = []

    # Mapping subfolder → category
    subfolder_to_category = {}
    for cat, subfolders in CATEGORIES.items():
        for sub in subfolders:
            subfolder_to_category[sub.lower()] = cat

    print('Step 1: Scan file per kategori...')
    for root, dirs, files in os.walk(input_folder):
        for f in files:
            full_path = Path(root) / f
            rel_path = full_path.relative_to(input_folder)
            rel_str = str(rel_path).replace('\\', '/')

            # Tentukan kategori dari subfolder pertama
            parts = rel_str.split('/')
            subfolder = parts[0].lower() if parts else ''

            if subfolder in subfolder_to_category:
                cat = subfolder_to_category[subfolder]
                if cat not in category_files:
                    category_files[cat] = []
                category_files[cat].append((full_path, rel_str))
            else:
                uncategorized_files.append((full_path, rel_str))

    # Hitung size per kategori
    category_sizes = {}
    for cat, files in category_files.items():
        total = sum(f[0].stat().st_size for f in files)
        category_sizes[cat] = total

    # File uncategorized → misc
    misc_size = sum(f[0].stat().st_size for f in uncategorized_files)

    print()
    print('Size per kategori:')
    for cat in sorted(category_sizes.keys(), key=lambda c: -category_sizes[c]):
        size = category_sizes[cat]
        file_count = len(category_files[cat])
        print(f'  {cat:15s}: {format_size(size):>10s} ({file_count} files)')

    if uncategorized_files:
        print(f'  {"misc":15s}: {format_size(misc_size):>10s} ({len(uncategorized_files)} files)')

    print()

    # Gabung kategori kecil ke misc
    final_categories = {}
    final_misc_files = list(uncategorized_files)

    for cat, files in category_files.items():
        if category_sizes[cat] < MISC_THRESHOLD:
            print(f'  Kategori "{cat}" ({format_size(category_sizes[cat])}) digabung ke misc (< {format_size(MISC_THRESHOLD)})')
            final_misc_files.extend(files)
        else:
            final_categories[cat] = files

    if final_misc_files:
        final_categories['misc'] = final_misc_files

    print()
    print(f'Final kategori yang akan di-zip: {len(final_categories)}')
    for cat in sorted(final_categories.keys()):
        files = final_categories[cat]
        total = sum(f[0].stat().st_size for f in files)
        print(f'  {cat:15s}: {format_size(total):>10s} ({len(files)} files)')

    print()

    # Step 2: Zip setiap kategori
    print('Step 2: Zip setiap kategori...')
    results = []

    for cat in sorted(final_categories.keys()):
        files = final_categories[cat]
        zip_name = f'sceneassets-{cat}.zip'
        zip_path = output_dir / zip_name

        print(f'  Zipping {zip_name}...')
        total_size = 0
        file_count = 0

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
            for full_path, arcname in files:
                # Strip sceneassets/ prefix kalau ada
                clean_arcname = arcname
                if clean_arcname.startswith('sceneassets/'):
                    clean_arcname = clean_arcname[len('sceneassets/'):]

                zf.write(full_path, clean_arcname)
                total_size += full_path.stat().st_size
                file_count += 1

                if file_count % 200 == 0:
                    print(f'    [{file_count}/{len(files)}] {format_size(total_size)}...')

        zip_size = zip_path.stat().st_size
        sha256 = sha256_file(zip_path)

        print(f'    ✓ {zip_name}: {format_size(zip_size)} ({file_count} files)')
        print(f'      SHA-256: {sha256}')

        results.append({
            'category': cat,
            'filename': zip_name,
            'path': str(zip_path),
            'original_size': total_size,
            'zip_size': zip_size,
            'sha256': sha256,
            'file_count': file_count,
        })

    print()
    print(f'=== Hasil Split ===')
    total_original = 0
    total_zip = 0
    for r in results:
        print(f'  {r["filename"]:35s} {format_size(r["zip_size"]):>10s}  (orig: {format_size(r["original_size"])}, {r["file_count"]} files)')
        print(f'    SHA-256: {r["sha256"]}')
        total_original += r['original_size']
        total_zip += r['zip_size']

    print()
    print(f'Total original: {format_size(total_original)}')
    print(f'Total zip:      {format_size(total_zip)}')
    print(f'Files created:  {len(results)}')
    print()

    # Step 3: Generate upload commands
    print('=== Langkah Selanjutnya ===')
    print('Upload setiap file ke release v26 dengan command:')
    print()
    for r in results:
        print(f'  dlavie-dlc upload-data "{r["path"]}" --sceneassets --category {r["category"]}')
    print()
    print('Atau upload manual via GitHub web UI:')
    print(f'  https://github.com/drmacze/DLavie-Launcher-Data/releases/upload/v26')
    print()

    # Save results to JSON untuk reference
    import json
    results_file = output_dir / 'split_results.json'
    with open(results_file, 'w') as f:
        json.dump({
            'input_folder': str(input_folder),
            'output_dir': str(output_dir),
            'total_original_size': total_original,
            'total_zip_size': total_zip,
            'files': results,
        }, f, indent=2)
    print(f'Results saved to: {results_file}')


def main():
    parser = argparse.ArgumentParser(
        description='DLavie Sceneassets Splitter — Pisahkan sceneassets besar jadi beberapa zip per kategori',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Split dari folder sceneassets
  python split_sceneassets_by_category.py /sdcard/FIFA16/data/sceneassets

  # Custom output dir
  python split_sceneassets_by_category.py /sdcard/FIFA16/data/sceneassets --output-dir /tmp/splits

Output:
  sceneassets-faces.zip      (HD faces)
  sceneassets-kit.zip        (HD kits)
  sceneassets-stadium.zip    (stadiums)
  sceneassets-hair.zip       (hairstyles)
  sceneassets-ball.zip       (balls)
  sceneassets-shoe.zip       (shoes)
  sceneassets-climate.zip    (climate/sky)
  sceneassets-misc.zip       (sisanya yang kecil)

Setiap file < 2GB supaya lolos GitHub Release limit.
""",
    )
    parser.add_argument('input_folder', help='Path ke folder sceneassets')
    parser.add_argument('--output-dir', default='/sdcard/dlavie-dlc/splits', help='Output directory (default: /sdcard/dlavie-dlc/splits)')

    args = parser.parse_args()
    split_sceneassets(args.input_folder, args.output_dir)


if __name__ == '__main__':
    main()
