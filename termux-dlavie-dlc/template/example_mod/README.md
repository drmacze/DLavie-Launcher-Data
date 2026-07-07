# Example Mod Template

Folder ini adalah template contoh untuk bikin DLC mod baru.

## Cara Pakai

1. Copy folder ini ke `/sdcard/dlavie-dlc/mods/DLC_NamaModAnda/`
2. Edit file yang ingin Anda modify (cl.ini, data/*.lua, dll)
3. Jalankan: `dlavie-dlc upload DLC_NamaModAnda 1.0.0 --note "Initial release"`

## Struktur Folder

```
DLC_NamaModAnda/
├── README.md           ← dokumentasi mod (opsional, tidak di-zip)
├── cl.ini              ← config utama FIFA 16
├── ai.ini              ← config AI (opsional)
├── data/
│   ├── flows/          ← Lua scripts untuk menu flow
│   │   └── mainflow/
│   │       └── gamemodes/
│   │           └── MainMenu/
│   │               └── Customize/
│   │                   └── Save/
│   │                       └── SaveHub.lua
│   └── ux/
│       └── Save/
│           └── SaveInfo.lua
└── manifest.json       ← info mod (opsional, tidak di-zip)
```

## Aturan Penting

- ✅ Hanya file game yang akan di-zip (cl.ini, data/, ai.ini, dll)
- ❌ File berikut akan di-skip otomatis: README.md, manifest.json, .gitignore
- ✅ Struktur folder harus sama dengan struktur di game data FIFA 16
- ✅ File akan diekstrak ke `/sdcard/Android/data/com.ea.gp.fifaworld/files/`

## Contoh Mod Lengkap

Lihat DLC_SaveMenuEnhancer di repo F16 sebagai contoh:
- https://github.com/drmacze/F16/tree/main/data/flows/mainflow/gamemodes/MainMenu/Customize
