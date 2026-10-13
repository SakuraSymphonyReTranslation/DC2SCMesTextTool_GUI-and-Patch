# DC2SC Patch — instalasi dan build

**Bahasa Indonesia** | [English](Readme_en.md)

Patch dan launcher ini dikhususkan untuk **Da Capo 2 Spring Celebration** (`D.C.II Spring Celebration ～ダ・カーポII～ スプリング セレブレイション`). Source utama: `src/dc2scpatch.cpp`.

## Instalasi

Unduh `Released_patch.rar` dari [Releases](https://github.com/SakuraSymphonyReTranslation/DC2SCMesTextTool_GUI-and-Patch/releases/latest), atau gunakan paket di `build/Released`.

`<GAME_DIR>` berarti folder instalasi pilihan pemain yang berisi `DC2SC.EXE` dan `AdvData`. Ganti placeholder ini dengan lokasi game Anda; tidak ada drive yang diwajibkan.

1. Tutup game, cadangkan berkas yang akan diganti, lalu ekstrak isi paket ke `<GAME_DIR>`.
2. Jalankan **`<GAME_DIR>\DC2SCLauncher.exe`** dengan working directory `<GAME_DIR>`; shortcut harus memakai folder itu pada **Start in**.
3. Launcher memuat DLL patch dan mencoba Locale Emulator JP, dengan fallback ke mode biasa jika pemuatan LE gagal.
4. Paket berisi `DC2SC.EXE`, `DC2SCLauncher.exe`, `DC2SCPatch.dll`, `DC2SCPatch.ini`, `LoaderDll.dll`, dan `LocaleEmulator.dll`.
5. Naskah terjemahan dipasang terpisah ke `id_Data\MES` atau `eng_data\MES` di dalam `<GAME_DIR>` sesuai pilihan bahasa pada `DC2SCPatch.ini` (`Language=1` untuk Indonesia).

Executable referensi yang diuji memiliki SHA256:

```text
cb1a9cdcd8c60b310fc7cdc4dab0bf544cd6d160853e8fa99afa92074d4039e4
```

## Fitur Patch Runtime

- **Bypass DVD Check:** AdvSys32 DVD check di-bypass dengan spoofing drive letter sehingga game dapat berjalan tanpa optical drive fisik di Windows 10/11 dan Linux (Wine/Proton).
- **File Redirection:** Redirection file skrip `.mes` ke folder `id_Data\MES` (atau `eng_data\MES`) tanpa perlu membongkar atau menimpa arsip asli game di `AdvData`.
- **Pengaturan Font & Scaling:** Pengaturan font dan rasio rendering teks dialog dikonfigurasi melalui `DC2SCPatch.ini` (`DialogueRenderScale=74`, `DialogueAdvanceScale=62`, `DialogueSpaceScale=24`).
- **Patcher Prompt Dialog:** Script di `tools/` menyediakan patch bitmap font untuk prompt konfirmasi sistem (Simpan, Muat, Keluar).

## Cara Build Patch (C++)

Gunakan x86 Native Tools Command Prompt untuk VS 2022:

```batch
build.bat
```

Atau manual dengan CMake:

```batch
mkdir build_cmake && cd build_cmake
cmake .. -G "NMake Makefiles" -DCMAKE_BUILD_TYPE=Release
nmake
```

Hasil build berupa `DC2SCLauncher.exe` dan `DC2SCPatch.dll`.
