# DC2SC MES Text Tool — GUI dan CLI

**Bahasa Indonesia** | [English](Readme_en.md)

Importer/exporter untuk **D.C.II Spring Celebration ～ダ・カーポII～ スプリング セレブレイション**.

Distribusi ini hanya mendukung **Da Capo 2 Spring Celebration** (`dc2sc`, versi MES `0x3B69`). GUI, CLI, tabel referensi, patch, dan launcher dikhususkan untuk game ini. Source utama patch: `DC2SCPatch a/src/dc2scpatch.cpp`.

## Unduhan dan folder instalasi

Unduh kedua paket terbaru dari [GitHub Releases](https://github.com/SakuraSymphonyReTranslation/DC2SCMesTextTool_GUI-and-Patch/releases/latest):

- **DC2SCMesTextTool_GUI.rar**: importer/exporter MES ↔ JSON, GUI dan CLI. Termasuk dokumentasi bahasa Indonesia dan Inggris.
- **Released_patch.rar**: launcher, DLL patch, INI, dan berkas pendukung runtime.

`<GAME_DIR>` berarti **folder utama instalasi game pilihan pemain**, yaitu folder yang berisi `DC2SC.EXE` dan `AdvData`. Ini placeholder dokumentasi: ganti dengan lokasi game Anda, tanpa tanda `<` dan `>`. Tidak ada drive atau lokasi instalasi wajib.

1. Tutup game dan simpan salinan berkas lama yang akan diganti, terutama executable dan `DC2SCPatch.ini`.
2. Ekstrak isi `Released_patch.rar` langsung ke `<GAME_DIR>`, sehingga `DC2SCLauncher.exe`, `DC2SCPatch.dll`, dan `DC2SCPatch.ini` berada di sebelah `DC2SC.EXE`.
3. Jalankan **`<GAME_DIR>\DC2SCLauncher.exe`** dengan working directory `<GAME_DIR>`. Jika memakai shortcut, isi **Start in** dengan folder tersebut.
4. Pilih bahasa yang sesuai pada pengaturan patch (`Language=1` untuk Indonesia, `Language=2` untuk Inggris, `Language=0` untuk Jepang asli). Berkas MES Indonesia ditempatkan di `<GAME_DIR>\id_Data\MES`; untuk bahasa Inggris, gunakan `<GAME_DIR>\eng_data\MES`.

```text
<GAME_DIR>/
├── DC2SC.EXE
├── DC2SCLauncher.exe
├── DC2SCPatch.dll
├── DC2SCPatch.ini
├── LoaderDll.dll
├── LocaleEmulator.dll
├── AdvData/
└── id_Data/
    └── MES/
```

Kedua RAR menyediakan tool dan runtime patch; keduanya tidak berisi seluruh naskah terjemahan. Folder source repositori boleh ditempatkan di mana saja. Paket patch juga tersedia di `DC2SCPatch a/build/Released` pada source.

Executable referensi yang diuji memiliki SHA256:

```text
cb1a9cdcd8c60b310fc7cdc4dab0bf544cd6d160853e8fa99afa92074d4039e4
```

## Buka aplikasi

Ekstrak `DC2SCMesTextTool_GUI.rar` ke folder pilihan Anda dan jalankan `DC2SCMesTextTool_GUI.exe`. Jika memakai source repositori, jalankan `bin\Release\net8.0-windows\DC2SCMesTextTool_GUI.exe`.
Paket siap pakai berada di folder: `bin\Release\net8.0-windows\DC2SCMesTextTool_GUI.rar`.
Aplikasi membutuhkan .NET 8 Desktop Runtime.

## Single File

**MES → JSON (exporter)**

1. Isi **Input MES/JSON** dengan MES asli.
2. Isi **Output**, atau kosongkan untuk membuat JSON di sebelah input.
3. Klik **Export (MES -> JSON)**.

Hasil default mengekspor nama karakter dan dialog berdasarkan format Circus MES:

```json
[
  { "message": "Narasi." },
  { "name": "Otome", "message": "「Dialog karakter.」" }
]
```

Ekspor dari tab Single File dan Batch menggunakan format di atas. Teks, nama Jepang/Indonesia, dan pemisah baris dipertahankan saat ekspor.

**JSON → MES (importer)**

1. Isi **Input MES/JSON** dengan JSON terjemahan.
2. File MES asli dicari otomatis jika berada di folder MES terkait atau di sebelah JSON.
3. Tentukan file **Output** yang berbeda dari MES asli.
4. Pilih **Word Wrap**: default `70` pada Single File, Batch, dan CLI; `0` mempertahankan teks/pemisah baris tanpa reflow.
5. Klik **Import (JSON -> MES)**.

Template asli dibutuhkan untuk menjaga struktur bytecode, token non-teks, dan alur label.

**Teks pilihan dan judul Scene Replay**

- Jika pilihan pada MES asli diawali `○`, importer mengembalikan tanda tersebut apabila terhapus dari JSON terjemahan.
- Spasi berulang pada pilihan dirapikan menjadi satu spasi, termasuk jarak setelah `○`. Spasi disimpan dalam bentuk yang aman untuk MES terenkripsi dan dikembalikan menjadi spasi biasa saat ekspor JSON.
- Judul Scene Replay dapat diganti melalui JSON lalu diimpor kembali ke MES. Ukuran judul dihitung otomatis oleh DLL saat game menampilkannya: judul panjang diperkecil agar tetap muat di kartu. Tidak perlu menambahkan pengaturan ukuran font di JSON atau membangun ulang patch.
- Setelah mengganti MES atau DLL, jalankan ulang game melalui `DC2SCLauncher.exe` agar perubahan dimuat.

## Batch

- **Batch Export:** isi **MES Folder** di kolom `MES Folder` dan tentukan output di `Output Folder`, lalu klik **Batch Export (MES -> JSON)**.
- **Batch Import:** isi **JSON Folder**, **MES Folder** asli, dan **Output Folder** yang berbeda, lalu klik **Batch Import (JSON -> MES)**.
- Nama file harus sama: misalnya `scene.json` memakai template `scene.mes`.
- File diproses satu per satu dan status serta kemajuan ditampilkan di kotak log bagian bawah.

## Layout dan patch runtime

- **`DC2SCPatch.dll`** disuntikkan secara otomatis oleh `DC2SCLauncher.exe`.
- **Bypass DVD check:** Engine AdvSys32 DC2SC melakukan pengecekan drive optik saat startup. Patch menyertakan spoofing drive sehingga game dapat berjalan mulus di sistem modern tanpa drive optik (termasuk Linux/Wine/Proton).
- **Font & Text Scaling:** Pengaturan rendering font dan scaling karakter Shift-JIS / alfabet dikonfigurasi melalui `DC2SCPatch.ini` (`DialogueRenderScale=74`, `DialogueAdvanceScale=62`, `DialogueSpaceScale=24`).
- **Layout Pilihan:** Jarak sebelum `○`, setelah tanda, dan antar kata dibuat lebih rapat. Pilihan panjang menyesuaikan ukuran dengan lebar kotaknya.
- **Efek Sakura:** Teks pilihan tetap utuh saat animasi daun sakura menggambar ulang sebagian layar.
- **Judul Scene Replay:** Judul Latin pada kartu replay menyesuaikan ukuran otomatis dengan ruang yang tersedia. Baris tanggal, ukuran popup, dan pengaturan textbox tetap menggunakan pengaturan semula.
- **File Redirection:** Arahkan pembacaan file skrip MES ke folder `id_Data\MES` (atau `eng_data\MES`) tanpa perlu menimpa berkas asli di `AdvData`.
- **System Prompt Localization:** Script pendukung di `DC2SCPatch a/tools/` menyediakan patch untuk popup teks konfirmasi (seperti Simpan, Muat, Keluar).

Petunjuk teknis patch tersedia di [README patch](DC2SCPatch%20a/README.md).

## Validasi dan encoding

- Engine DC2SC menggunakan encoding **Shift-JIS (CP932)**.
- String bytecode terenkripsi disimpan dengan mengurangi setiap byte sebesar `0x20`, lalu dibaca kembali dengan menambahkan `0x20` (modulo 256).
- Label MES dihitung ulang berdasarkan struktur header tabel label Offset1 (`labelCount * 4 + 4`).
- Karakter yang tidak didukung Shift-JIS divalidasi agar tidak menyebabkan teks rusak atau crash di dalam game.

## CLI

Dari folder executable:

```powershell
.\DC2SCMesTextTool_GUI.exe export "scene.mes" "scene.json"
.\DC2SCMesTextTool_GUI.exe import "scene.json" "original\scene.mes" "new\scene.mes" -w 70
.\DC2SCMesTextTool_GUI.exe batch-export "original_mes_folder" "json_output"
.\DC2SCMesTextTool_GUI.exe batch-import "json_folder" "original_mes_folder" "output_mes_folder" -w 70
```

`-w` mengatur batas word wrap (default: 70, `0` untuk tanpa wrap). Drag-and-drop file `.mes` langsung ke jendela GUI juga didukung untuk ekspor cepat.

## Build

Dari folder source proyek:

```powershell
dotnet build -c Release
```

Build GUI membutuhkan .NET 8 SDK. Untuk build patch DLL dan launcher C++, lihat petunjuk di [README patch](DC2SCPatch%20a/README.md).

Solution Visual Studio 2022 tersedia langsung di `DC2SCPatch a/build/DC2SCPatch.sln`. Pilih **Release | Win32**, lalu **Build → Build Solution**. Seluruh isi folder `build` disertakan di repository; `build/Release` berisi hasil kompilasi, sedangkan `build/Released` berisi paket distribusi. Setelah clone ke lokasi lain, buat ulang solution dengan langkah CMake pada README patch agar path sesuai komputer Anda.
