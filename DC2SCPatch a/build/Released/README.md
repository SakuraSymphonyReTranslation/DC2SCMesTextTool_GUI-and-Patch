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
5. Naskah terjemahan dipasang terpisah ke `id_Data\MES` atau `eng_data\MES` di dalam `<GAME_DIR>` sesuai pilihan bahasa pada `DC2SCPatch.ini` (`Language=1` untuk Indonesia, `Language=2` untuk Inggris, `Language=0` untuk Jepang asli).

Executable referensi yang diuji memiliki SHA256:

```text
cb1a9cdcd8c60b310fc7cdc4dab0bf544cd6d160853e8fa99afa92074d4039e4
```

## Fitur Patch Runtime

- **Bypass DVD Check:** AdvSys32 DVD check di-bypass dengan spoofing drive letter sehingga game dapat berjalan tanpa optical drive fisik di Windows 10/11 dan Linux (Wine/Proton).
- **File Redirection:** Redirection file skrip `.mes` ke folder `id_Data\MES` (atau `eng_data\MES`) tanpa perlu membongkar atau menimpa arsip asli game di `AdvData`.
- **Pengaturan Font & Scaling:** Pengaturan font dan rasio rendering teks dialog dikonfigurasi melalui `DC2SCPatch.ini` (`DialogueRenderScale=74`, `DialogueAdvanceScale=62`, `DialogueSpaceScale=24`).
- **Layout Pilihan:** Teks pilihan Latin memakai jarak yang lebih rapat di sekitar `○` dan antar kata, serta menyesuaikan ukuran jika terlalu panjang.
- **Redraw Sakura:** Layout memakai batas kotak pilihan yang tetap, sehingga teks tidak hilang saat efek sakura menggambar ulang area kecil layar.
- **Judul Scene Replay:** Judul Latin diperkecil otomatis agar muat di kartu, dengan ukuran normal maksimal 16 piksel. Ukuran dihitung dari teks yang sedang ditampilkan; perubahan judul melalui impor JSON/MES tidak memerlukan build ulang DLL. Pertahankan penanda teks kecil `@s` jika muncul dalam hasil ekspor.
- **Patcher Prompt Dialog:** Script di `tools/` menyediakan patch bitmap font untuk prompt konfirmasi sistem (Simpan, Muat, Keluar).

Perbaikan layout pilihan dan judul replay berlaku pada mode terjemahan (`Language=1` atau `2`). Baris tanggal replay, ukuran popup, dan pengaturan textbox tidak diubah oleh layout ini. Jalankan ulang game melalui launcher setelah mengganti MES atau DLL.

## Cara Build Patch (C++)

Gunakan **Visual Studio 2022** dengan workload **Desktop development with C++**, Windows SDK, serta **CMake 3.24 atau lebih baru**.

1. Buka `build/DC2SCPatch.sln`.
2. Pilih konfigurasi **Release** dan platform **Win32**.
3. Klik **Build → Build Solution** (`Ctrl+Shift+B`).

Hasil build berada di `build/Release/DC2SCLauncher.exe` dan `build/Release/DC2SCPatch.dll`. Folder `build/Released` menyimpan paket distribusi dan tidak diperbarui otomatis oleh kompilasi.

Seluruh isi `build` disertakan di repository, termasuk solution, project, cache, dan hasil kompilasi. Cache dan project CMake menyimpan path komputer pembuatnya. **Setelah clone atau memindahkan source**, jalankan perintah berikut dari folder `DC2SCPatch a` untuk membuat ulang solution sesuai lokasi dan toolchain komputer Anda:

```batch
cmake --fresh -S . -B build -G "Visual Studio 17 2022" -A Win32
cmake --build build --config Release --parallel
```

Atau jalankan script yang melakukan konfigurasi dan build tersebut:

```batch
build.bat
```

Salin launcher dan DLL hasil build ke `<GAME_DIR>` untuk menggunakannya. Source layout pilihan dan replay berada di `src/choice_layout.h`; uji layout tersedia melalui `tools/build_choice_test.cmd`.
